import inspect
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from functools import wraps

import pandas as pd
from google.auth.api_key import Credentials
from google.oauth2.gdch_credentials import ServiceAccountCredentials


def root_directory() -> str:
    """
    Determine the root directory of the project. It checks if it's running in a Docker container and adjusts accordingly.

    Returns:
    - str: The path to the root directory of the project.
    """

    # Check if running in a Docker container
    if os.path.exists('/.dockerenv'):
        # If inside a Docker container, use '/app' as the root directory
        return '/app'

    # If not in a Docker container, try to use the git command to find the root directory
    try:
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], stderr=subprocess.STDOUT)
        return git_root.strip().decode('utf-8')
    except subprocess.CalledProcessError:
        # Git command failed, which might mean we're not in a Git repository
        # Fall back to manual traversal
        pass
    except Exception as e:
        # Some other error occurred while trying to execute git command
        print(f"An error occurred while trying to find the Git repository root: {e}")

    # Manual traversal if git command fails
    current_dir = os.getcwd()
    root = os.path.abspath(os.sep)
    traversal_count = 0  # Track the number of levels traversed

    while current_dir != root:
        try:
            if 'src' in os.listdir(current_dir):
                print(f"Found root directory: {current_dir}")
                return current_dir
            current_dir = os.path.dirname(current_dir)
            traversal_count += 1
            print(f"Traversal count # {traversal_count}")
            if traversal_count > 10:
                raise Exception("Exceeded maximum traversal depth (more than 10 levels).")
        except PermissionError as e:
            # Could not access a directory due to permission issues
            raise Exception(f"Permission denied when accessing directory: {current_dir}") from e
        except FileNotFoundError as e:
            # The directory was not found, which should not happen unless the filesystem is changing
            raise Exception(f"The directory was not found: {current_dir}") from e
        except OSError as e:
            # Handle any other OS-related errors
            raise Exception("An OS error occurred while searching for the Git repository root.") from e

    # If we've reached this point, it means we've hit the root of the file system without finding a .git directory
    raise Exception("Could not find the root directory of the project. Please make sure you are running this script from within a Git repository.")


def timeit(func):
    """
    A decorator that logs the time a function takes to execute along with the directory and filename.

    Args:
        func (callable): The function being decorated.

    Returns:
        callable: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        The wrapper function to execute the decorated function and log its execution time and location.

        Args:
            *args: Variable length argument list to pass to the decorated function.
            **kwargs: Arbitrary keyword arguments to pass to the decorated function.

        Returns:
            The value returned by the decorated function.
        """
        if os.getenv('ENVIRONMENT') == 'LOCAL':
            # Get the current file's path and extract directory and filename
            file_path = inspect.getfile(func)
            directory, filename = os.path.split(file_path)
            dir_name = os.path.basename(directory)

            # Log start of function execution
            logging.info(f"{dir_name}.{filename}.{func.__name__} STARTED.")
            start_time = time.time()

            # Call the decorated function and store its result
            result = func(*args, **kwargs)

            end_time = time.time()
            elapsed_time = end_time - start_time
            minutes, seconds = divmod(elapsed_time, 60)

            # Log end of function execution
            logging.info(f"{dir_name}.{filename}.{func.__name__} COMPLETED, took {int(minutes)} minutes and {seconds:.2f} seconds to run.\n")

            return result
        else:
            # If not in 'LOCAL' environment, just call the function without timing
            return func(*args, **kwargs)

    return wrapper


def authenticate_service_account(service_account_file: str) -> Credentials:
    """Authenticates using service account and returns the session."""

    credentials = ServiceAccountCredentials.from_service_account_file(
        service_account_file,
        scopes=["https://www.googleapis.com/auth/youtube.readonly"]
    )
    return credentials


def find_closest_match(video_title, df_titles):
    max_overlap = 0
    best_match = None
    for title in df_titles:
        # Ensure title is a string before iterating
        title_str = str(title)
        overlap = sum(1 for a, b in zip(video_title, title_str) if a == b)
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = title_str
    return best_match


def move_remaining_mp3_to_their_subdirs():
    # Load the DataFrame
    videos_path = f"{root_directory()}/datasets/evaluation_data/youtube_videos.csv"
    youtube_videos_df = pd.read_csv(videos_path)
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace(' +', ' ', regex=True)
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace('"', '', regex=True)

    # Get a list of all mp3 files in the directory and subdirectories
    mp3_files = []
    for subdir, dirs, files in os.walk(f"{root_directory()}/datasets/evaluation_data/diarized_youtube_content_2023-10-06"):
        for file in files:
            if file.endswith(".mp3"):
                mp3_files.append(os.path.join(subdir, file))

    df_titles = youtube_videos_df['title'].tolist()
    # Process each mp3 file
    for mp3_file in mp3_files:
        # Extract the segment after the last "/"
        video_title = mp3_file.split('/')[-1].rsplit('.', 1)[0]
        # Replace double spaces with a single space
        video_title = video_title.replace('  ', ' ').strip()

        # Check if mp3 file is already in a directory matching its name
        containing_dir = os.path.basename(os.path.dirname(mp3_file))
        if video_title == containing_dir:
            continue

        best_match = find_closest_match(video_title, df_titles)
        video_row = youtube_videos_df[youtube_videos_df['title'] == best_match]

        if not video_row.empty:
            published_date = video_row.iloc[0]['published_date']
            new_dir_name = f"{published_date}_{video_title}"
            new_dir_path = os.path.join(os.path.dirname(mp3_file), new_dir_name)
            os.makedirs(new_dir_path, exist_ok=True)
            new_file_name = f"{published_date}_{video_title}.mp3"
            new_file_path = os.path.join(new_dir_path, new_file_name)
            print(f"Moved video {best_match} to {new_file_path}!")
            shutil.move(mp3_file, new_file_path)
        else:
            print(f"No matching video title found in DataFrame for: {video_title}")


def move_remaining_txt_to_their_subdirs():
    # Load the DataFrame
    videos_path = f"{root_directory()}/datasets/evaluation_data/youtube_videos.csv"
    youtube_videos_df = pd.read_csv(videos_path)
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace(' +', ' ', regex=True)
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace('"', '', regex=True)

    # Get a list of all txt files in the directory and subdirectories
    txt_files = []
    for subdir, dirs, files in os.walk(f"{root_directory()}/datasets/evaluation_data/diarized_youtube_content_2023-10-06"):
        for file in files:
            if file.endswith("_diarized_content_processed_diarized.txt"):
                txt_files.append(os.path.join(subdir, file))

    df_titles = youtube_videos_df['title'].tolist()
    # Process each txt file
    for txt_file in txt_files:
        # Extract the segment after the last "/"
        extension = "_diarized_content_processed_diarized.txt"
        video_title = txt_file.replace(extension, '').split('/')[-1].rsplit('.', 1)[0]
        # Replace double spaces with a single space
        video_title = video_title.replace('  ', ' ').strip()

        # video_row = youtube_videos_df[youtube_videos_df['title'].str.contains(video_title, case=False, na=False, regex=False)]
        best_match = find_closest_match(video_title, df_titles)
        video_row = youtube_videos_df[youtube_videos_df['title'] == best_match]

        if not video_row.empty:
            published_date = video_row.iloc[0]['published_date']
            new_dir_name = f"{published_date}_{video_title}"

            # Check if txt file is already in a directory matching its name
            containing_dir = os.path.basename(os.path.dirname(txt_file))
            if new_dir_name == containing_dir:
                continue

            new_dir_path = os.path.join(os.path.dirname(txt_file), new_dir_name)
            os.makedirs(new_dir_path, exist_ok=True)
            new_file_name = f"{published_date}_{video_title}{extension}"
            new_file_path = os.path.join(new_dir_path, new_file_name)
            if os.path.exists(new_file_path):
                print(f"Deleted {txt_file} because {new_file_path} already exists")
                os.remove(txt_file)
            else:
                print(f"Moved video {txt_file} to {new_file_path}!")
                shutil.move(txt_file, new_file_path)
        else:
            print(f"No matching video title found in DataFrame for: {video_title}")


def move_remaining_json_to_their_subdirs():
    # Load the DataFrame
    videos_path = f"{root_directory()}/datasets/evaluation_data/youtube_videos.csv"
    youtube_videos_df = pd.read_csv(videos_path)
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace(' +', ' ', regex=True)
    youtube_videos_df['title'] = youtube_videos_df['title'].str.replace('"', '', regex=True)

    # Get a list of all json files in the directory and subdirectories
    json_files = []
    for subdir, dirs, files in os.walk(f"{root_directory()}/datasets/evaluation_data/diarized_youtube_content_2023-10-06"):
        for file in files:
            if file.endswith("_diarized_content.json"):
                json_files.append(os.path.join(subdir, file))

    df_titles = youtube_videos_df['title'].tolist()
    # Process each json file
    for json_file in json_files:
        # Extract the segment after the last "/"
        extension = "_diarized_content.json"
        video_title = json_file.replace(extension, '').split('/')[-1].rsplit('.', 1)[0]
        # Replace double spaces with a single space
        video_title = video_title.replace('  ', ' ').strip()

        # video_row = youtube_videos_df[youtube_videos_df['title'].str.contains(video_title, case=False, na=False, regex=False)]
        best_match = find_closest_match(video_title, df_titles)
        video_row = youtube_videos_df[youtube_videos_df['title'] == best_match]

        if not video_row.empty:
            published_date = video_row.iloc[0]['published_date']
            new_dir_name = f"{published_date}_{video_title}"

            # Check if json file is already in a directory matching its name
            containing_dir = os.path.basename(os.path.dirname(json_file))
            if new_dir_name == containing_dir:
                continue

            new_dir_path = os.path.join(os.path.dirname(json_file), new_dir_name)
            os.makedirs(new_dir_path, exist_ok=True)
            new_file_name = f"{published_date}_{video_title}{extension}"
            new_file_path = os.path.join(new_dir_path, new_file_name)
            if os.path.exists(new_file_path):
                print(f"Deleted {json_file} because {new_file_path} already exists")
                os.remove(json_file)
            else:
                print(f"Moved video {json_file} to {new_file_path}!")
                shutil.move(json_file, new_file_path)
        else:
            print(f"No matching video title found in DataFrame for: {video_title}")


def merge_directories(base_path):
    '''
    This function walks through all subdirectories and merges the contents of directories that have
    names differing only by the pipe character used, from fullwidth to ASCII. Files from the fullwidth
    pipe directory are moved to the ASCII pipe directory, and if a file with the same name exists, the
    file from the fullwidth pipe directory is deleted. After the merge, the fullwidth pipe directory is
    deleted if empty.

    Args:
        base_path: The base directory path to start searching from.

    Returns: None
    '''

    # Helper function to rename the pipe character
    def standardize_name(dir_or_file_name):
        return dir_or_file_name.replace('：', ':')

    # Track directories to be removed after processing
    dirs_to_remove = []

    # Walk through the directory structure
    for root, dirs, _ in os.walk(base_path):
        # Map of standard directory names to their full paths
        standard_dirs = {}

        # First pass to fill in the mapping
        for dir_name in dirs:
            standard_dirs[standardize_name(dir_name)] = os.path.join(root, dir_name)

        # Second pass to perform the merging
        for dir_name in dirs:
            standard_name = standardize_name(dir_name)
            src = os.path.join(root, dir_name)
            dst = standard_dirs[standard_name]

            # Only proceed if the directory names actually differ (by the pipe character)
            if src != dst:
                if not os.path.exists(dst):
                    # If the destination doesn't exist, simply rename the directory
                    os.rename(src, dst)
                    print(f"Renamed {src} to {dst}")
                else:
                    # Merge contents
                    for item in os.listdir(src):
                        src_item = os.path.join(src, item)
                        dst_item = os.path.join(dst, standardize_name(item))
                        if os.path.exists(dst_item):
                            # If there is a conflict, delete the source item
                            os.remove(src_item)
                            print(f"Deleted due to conflict: {src_item}")
                        else:
                            shutil.move(src_item, dst_item)
                            print(f"Moved {src_item} to {dst_item}")

                    # Add to list of directories to remove if they are empty
                    dirs_to_remove.append(src)

    # Remove the source directories if they are empty
    for dir_to_remove in dirs_to_remove:
        if not os.listdir(dir_to_remove):
            os.rmdir(dir_to_remove)
            print(f"Removed empty directory: {dir_to_remove}")
        else:
            print(f"Directory {dir_to_remove} is not empty after merge. Please check contents.")


def fullwidth_to_ascii(char):
    """Converts a full-width character to its ASCII equivalent."""
    # Full-width range: 0xFF01-0xFF5E
    # Corresponding ASCII range: 0x21-0x7E
    fullwidth_offset = 0xFF01 - 0x21
    return chr(ord(char) - fullwidth_offset) if 0xFF01 <= ord(char) <= 0xFF5E else char


def clean_fullwidth_characters(base_path):
    for root, dirs, files in os.walk(base_path, topdown=False):  # topdown=False to start from the innermost directories
        # First handle the files in the directories
        for file in files:
            new_file_name = ''.join(fullwidth_to_ascii(char) for char in file)
            original_file_path = os.path.join(root, file)
            new_file_path = os.path.join(root, new_file_name)

            if new_file_name != file:
                if os.path.exists(new_file_path):
                    # If the ASCII version exists, delete the full-width version
                    os.remove(original_file_path)
                    print(f"Deleted {original_file_path}")
                else:
                    # Otherwise, rename the file
                    os.rename(original_file_path, new_file_path)
                    print(f"Renamed {original_file_path} to {new_file_path}")

        # Then handle directories
        for dir in dirs:
            new_dir_name = ''.join(fullwidth_to_ascii(char) for char in dir)
            original_dir_path = os.path.join(root, dir)
            new_dir_path = os.path.join(root, new_dir_name)

            if new_dir_name != dir:
                if os.path.exists(new_dir_path):
                    # If the ASCII version exists, delete the full-width version and its contents
                    shutil.rmtree(original_dir_path)
                    print(f"Deleted directory and all contents: {original_dir_path}")
                else:
                    # Otherwise, rename the directory
                    os.rename(original_dir_path, new_dir_path)
                    print(f"Renamed {original_dir_path} to {new_dir_path}")


def delete_mp3_if_text_or_json_exists(base_path):
    for root, dirs, _ in os.walk(base_path):
        for dir in dirs:
            subdir_path = os.path.join(root, dir)
            # Get a list of files in the current subdirectory
            files = os.listdir(subdir_path)
            # Filter out .mp3, .txt and .json files
            mp3_files = [file for file in files if file.endswith('.mp3')]
            txt_json_files = [file for file in files if file.endswith('.txt') or file.endswith('.json')]

            if mp3_files:
                # If there are both .mp3 and (.txt or .json) files, delete the .mp3 files
                if txt_json_files:
                    for mp3_file in mp3_files:
                        mp3_file_path = os.path.join(subdir_path, mp3_file)
                        print(f"Deleted .mp3 file: {mp3_file_path}")
                        os.remove(mp3_file_path)
                else:
                    # If there are only .mp3 files, print their names and containing directory
                    for mp3_file in mp3_files:
                        pass
                        # print(f".mp3 file without .txt or .json: {mp3_file} in directory {subdir_path}")


def start_logging(log_prefix):
    # Ensure that root_directory() is defined and returns the path to the root directory

    logs_dir = f'{root_directory()}/logs/txt'

    # Create a 'logs' directory if it does not exist, with exist_ok=True to avoid FileExistsError
    os.makedirs(logs_dir, exist_ok=True)

    # Get the current date and time
    now = datetime.now()
    timestamp_str = now.strftime('%Y-%m-%d_%H-%M')

    # Set up the logging level
    root_logger = logging.getLogger()

    # If handlers are already present, we can disable them.
    if root_logger.hasHandlers():
        # Clear existing handlers from the root logger
        root_logger.handlers.clear()

    root_logger.setLevel(logging.INFO)

    # Add handler to log messages to a file
    log_filename = f'{logs_dir}/{timestamp_str}_{log_prefix}.log'
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(file_handler)

    # Add handler to log messages to the standard output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)

    # Now, any logging.info() call will append the log message to the specified file and the standard output.
    logging.info(f'********* {log_prefix} LOGGING STARTED *********')


