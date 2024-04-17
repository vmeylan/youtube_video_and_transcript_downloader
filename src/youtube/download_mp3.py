import asyncio
import itertools
import json
import os
import argparse
from typing import List, Optional
from dotenv import load_dotenv
import pandas as pd
import yt_dlp as ydlp
from yt_dlp import DownloadError
import logging

from src.utils.utils import root_directory
from src.utils.download import get_channel_id, get_video_info
from src.constants_and_keywords_to_filter import YOUTUBE_VIDEO_DIRECTORY
from src.utils.utils import authenticate_service_account, move_remaining_mp3_to_their_subdirs, clean_fullwidth_characters, merge_directories, delete_mp3_if_text_or_json_exists, start_logging

from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=os.cpu_count())
api_key = os.environ.get('YOUTUBE_API_KEY')
if not api_key:
    raise ValueError("No API key provided. Please provide an API key via command line argument or .env file.")

# Load environment variables from the .env file
load_dotenv()
DOWNLOAD_AUDIO = os.environ.get('DOWNLOAD_AUDIO', 'True').lower() == 'true'
start_logging(f"download_mp3s")
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)


def chunked_iterable(iterable, size):
    """Splits an iterable into chunks of a specified size."""
    iterator = iter(iterable)
    while True:
        chunk = list(itertools.islice(iterator, size))
        if not chunk:
            break
        yield chunk


def download_video(url, ydl_opts, retries=3):
    while retries > 0:
        with ydlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                logging.info(f"Downloaded video: {url}")
                break  # Exit the loop if download succeeds
            except DownloadError:
                logging.warning(f"Download error for {url}. Retrying... {retries} attempts left.")
            except Exception as e:
                logging.warning(f"Error downloading {url}: {e}")
        retries -= 1  # Decrement the number of retries after an exception


async def download_audio_batch(video_infos: List[dict], ydl_opts: dict):
    """
    Download a batch of videos in parallel using threads.
    """
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(executor, download_video, info['url'], ydl_opts)
        for info in video_infos
    ]
    for future in futures:
        try:
            await future  # Use await to get the result of the future
        except Exception as e:
            # Handle exceptions from within the thread
            logging.error(f"An error occurred: {e}")


def filter_videos_in_dataframe(video_info_list, youtube_videos_df):
    # Normalize titles in the dataframe
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace(' +', ' ', regex=True).str.replace('"', '', regex=False)

    # Extract titles from the video info list
    titles = [video['title'] for video in video_info_list]

    # Create a mask for videos that are in the DataFrame
    mask = youtube_videos_df['title'].isin(titles)

    # Get the titles present in the DataFrame
    titles_in_df = youtube_videos_df[mask]

    # Filter and return videos that are in DataFrame
    return titles_in_df


async def video_valid_for_processing(channel_name, video_title, dir_path):
    try:
        normalized_video_title = video_title.replace('/', '_')
        titles_to_avoid = ['livestream', 'live stream', 'live']
        for title in titles_to_avoid:
            if title in normalized_video_title.lower():
                return False

        # Function to check for the title's existence in files
        def title_exists_in_files(directory, suffix):
            for filename in os.listdir(directory):
                if normalized_video_title in filename and filename.endswith(suffix):
                    return True
            return False

        # Recursively check in dir_path and its subdirectories
        for root, dirs, files in os.walk(dir_path):
            if (
                    title_exists_in_files(root, ".mp3") or
                    title_exists_in_files(root, "_diarized_content.json") or
                    title_exists_in_files(root, "_diarized_content_processed_diarized.txt") or
                    title_exists_in_files(root, "_content_processed_diarized.txt")
            ):
                # logging.info(f"video_valid_for_processing: {video_title} is already processed")
                return False
        logging.info(f"[{channel_name}] video_valid_for_processing: [{video_title}] is not processed yet, adding to the list!")
        return True
    except Exception as e:
        logging.warning(f"Exception in video_valid_for_processing: {e}")
        return False


async def prepare_download_info(video_info, dir_path, video_title):
    strlen = len("yyyy-mm-dd")
    published_at = video_info['publishedAt'].replace(':', '-').replace('.', '-')[:strlen]
    video_title = f"{published_at}_{video_title}"

    # Create a specific directory for this video if it doesn't exist
    video_dir_path = os.path.join(dir_path, video_title)
    if not os.path.exists(video_dir_path):
        os.makedirs(video_dir_path)

    audio_file_path = os.path.join(video_dir_path, f'{video_title}.mp3')
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{video_dir_path}/{video_title}.%(ext)s',
    }
    return ydl_opts, audio_file_path


async def process_video_batches(channel_name, video_info_list, dir_path, youtube_videos_df, batch_size=50):
    video_batches = list(chunked_iterable(video_info_list, batch_size))
    # TODO 2023-10-31: fix somehow the addition of spaces before colons : e.g. for DVT and for Defi panel
    #  The different pipes somehow. Check the match method in utils.py
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{dir_path}/%(title)s.%(ext)s',
    }

    tasks = []
    for batch_info in video_batches:
        filtered_videos = filter_videos_in_dataframe(batch_info, youtube_videos_df)
        valid_videos = []
        for index, row in filtered_videos.iterrows():
            video_dict = row.to_dict()
            is_video_Valid = await video_valid_for_processing(channel_name, video_dict['title'], dir_path)
            if is_video_Valid:
                valid_videos.append(video_dict)
        if len(valid_videos) > 1:
            logging.info(f"[{channel_name}] valid videos: {valid_videos}")

        if valid_videos:
            # Since download_audio_batch is now an async function, we directly add it to the task list
            task = asyncio.create_task(download_audio_batch(valid_videos, ydl_opts))
            tasks.append(task)

    # Now we run the download tasks concurrently.
    await asyncio.gather(*tasks)


async def process_video_batches_async(channel_id, channel_name, credentials, youtube_videos_df):
    logging.info(f"Processing channel: {channel_name}")
    dir_path = YOUTUBE_VIDEO_DIRECTORY
    # Get video information from the channel
    video_info_list = get_video_info(credentials, api_key, channel_id)

    # Create a 'data' directory if it does not exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Create a subdirectory for the current channel if it does not exist
    dir_path += f'{channel_name}'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    await process_video_batches(channel_name, video_info_list, dir_path, youtube_videos_df)


async def run(api_key: str, yt_channels: Optional[List[str]] = None, yt_playlists: Optional[List[str]] = None):
    """
    Run function that takes a YouTube Data API key and a list of YouTube channel names, fetches video transcripts,
    and saves them as .txt files in a data directory.

    Args:
        yt_playlists:
        api_key (str): Your YouTube Data API key.
        yt_channels (List[str]): A list of YouTube channel names.
    """
    clean_mp3s()
    service_account_file = os.environ.get('SERVICE_ACCOUNT_FILE')
    credentials = None

    if service_account_file:
        credentials = authenticate_service_account(service_account_file)
        logging.info("Service account file found. Proceeding with public channels, playlists, or private videos if accessible via Google Service Account.")
    else:
        logging.info("No service account file found. Proceeding with public channels or playlists.")

    # Create a dictionary with channel IDs as keys and channel names as values
    # Define the path for storing the mapping between channel names and their IDs
    channel_mapping_filepath = f"{root_directory()}/datasets/evaluation_data/channel_handle_to_id_mapping.json"

    # Load existing mappings if the file exists, or initialize an empty dictionary
    channel_name_to_id = {}  # Initialize regardless
    if os.path.exists(channel_mapping_filepath):
        with open(channel_mapping_filepath, 'r', encoding='utf-8') as file:
            channel_name_to_id = json.load(file)

    yt_id_name = {get_channel_id(credentials=credentials, api_key=api_key, channel_name=name, channel_name_to_id=channel_name_to_id): name for name in yt_channels}

    videos_path = f"{root_directory()}/datasets/evaluation_data/youtube_videos.csv"
    youtube_videos_df = pd.read_csv(videos_path)

    # Iterate through the dictionary of channel IDs and channel names
    await asyncio.gather(*(process_video_batches_async(channel_id, channel_name, credentials, youtube_videos_df)
                           for channel_id, channel_name in yt_id_name.items()))

    # Iterate through the dictionary of channel IDs and channel names

    # if yt_playlists:
    #     await asyncio.gather(*(process_video_batches_async(channel_id, channel_name, credentials, youtube_videos_df)
    #                            for channel_id, channel_name in yt_id_name.items()))
    #     for playlist_id in yt_playlists:
    #         playlist_title = get_playlist_title(credentials, api_key, playlist_id)
    #         # Ensure the title is filesystem-friendly (replacing slashes, for example)
    #         playlist_title = playlist_title.replace('/', '_') if playlist_title else f"playlist_{playlist_id}"
    #
    #         video_info_list = get_videos_from_playlist(credentials, api_key, playlist_id)
    #
    #         if not os.path.exists(dir_path):
    #             os.makedirs(dir_path)
    #
    #         dir_path += f'/{playlist_title}'
    #         if not os.path.exists(dir_path):
    #             os.makedirs(dir_path)
    #
    #         await process_video_batches(channel_name, video_info_list, dir_path, youtube_videos_df)

    # clean up because downloaded file names have full-width characters instead of ASCII
    clean_mp3s()


def clean_mp3s():
    directory = f"{root_directory()}/datasets/evaluation_data/diarized_youtube_content_2023-10-06"
    delete_mp3_if_text_or_json_exists(directory)
    clean_fullwidth_characters(directory)
    move_remaining_mp3_to_their_subdirs()
    merge_directories(directory)


def get_youtube_channels_from_file(file_path):
    with open(file_path, 'r') as file:
        channels = file.read().split(',')
    return channels


def main():
    parser = argparse.ArgumentParser(description='Fetch YouTube video transcripts.')
    parser.add_argument('--api_key', type=str, help='YouTube Data API key')  # to be moved back to main() to use CLI arguments
    parser.add_argument('--channels', nargs='+', type=str, help='YouTube channel names or IDs')
    parser.add_argument('--playlists', nargs='+', type=str, help='YouTube playlist IDs')

    args = parser.parse_args()

    yt_channels_file = os.path.join(root_directory(), 'datasets/evaluation_data/youtube_channel_handles.txt')

    # Fetch the yt_channels from the file
    yt_channels = get_youtube_channels_from_file(yt_channels_file)

    yt_playlists = args.playlists or os.environ.get('YOUTUBE_PLAYLISTS')
    if yt_playlists:
        yt_playlists = [playlist.strip() for playlist in yt_playlists.split(',')]

    if not yt_channels and not yt_playlists:
        raise ValueError(
            "No channels or playlists provided. Please provide channel names, IDs, or playlist IDs via command line argument or .env file.")

    asyncio.run(run(api_key, yt_channels, yt_playlists))


if __name__ == '__main__':
    main()

