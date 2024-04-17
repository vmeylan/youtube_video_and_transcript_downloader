import json
import logging
import os
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dotenv import load_dotenv

from src.constants_and_keywords_to_filter import YOUTUBE_VIDEO_DIRECTORY

load_dotenv()
api_keys = os.environ.get('ASSEMBLY_AI_API_KEYS')  # Expecting a comma-separated list of API keys

if not api_keys:
    raise EnvironmentError("ASSEMBLY_AI_API_KEYS environment variable not found. Please set it before running the script.")

api_keys = api_keys.split(',')


class No200HTTPFilter(logging.Filter):
    def filter(self, record):
        # Assuming the log message is structured in a way that includes the status code directly
        if "HTTP/1.1 200 OK" in record.getMessage():
            return False  # Do not log
        return True  # Log all other messages

# Assuming a logger is set up somewhere in the script


def set_api_key(api_key):
    import assemblyai as aai
    aai.settings.api_key = api_key


def random_sleep(min_seconds=0.5, max_seconds=2.5):
    time.sleep(random.uniform(min_seconds, max_seconds))


def is_valid_filename(filename):
    return re.match(r'^\d{4}-\d{2}-\d{2}_', filename)


def utterance_to_dict(utterance) -> dict:
    return {
        'text': utterance.text,
        'start': utterance.start,
        'end': utterance.end,
        'confidence': utterance.confidence,
        'channel': utterance.channel,
        'speaker': utterance.speaker,
        'words': [{
            'text': word.text,
            'start': word.start,
            'end': word.end,
            'confidence': word.confidence,
            'channel': word.channel,
            'speaker': word.speaker
        } for word in utterance.words]
    }


def transcribe_and_save(api_key_file_path):
    api_key, file_path = api_key_file_path
    set_api_key(api_key)
    random_sleep()
    try:
        transcript_file_path = os.path.splitext(file_path)[0] + "_diarized_content.json"

        if os.path.exists(transcript_file_path):
            logging.info(f"Content for {file_path.split('/')[-1].replace('.mp3', '.json')} already diarized. Skipping.")
            return

        if not os.path.exists(file_path):
            logging.warning(f"File {file_path} not found.")
            return


        # Split the file_path into segments
        path_segments = file_path.split('/')

        # Extract "@EthereumProtocol" and ".mp3" file name based on their fixed positions
        channel_name = path_segments[-3]  # Assuming "@EthereumProtocol" is always two directories up from the file
        file_name = path_segments[-1]  # The .mp3 file name is the last segment

        # Similarly for the JSON path if needed, adjust based on how you get or store the transcript_file_path
        transcript_file_name = os.path.basename(transcript_file_path)  # Gets the file name from the full path

        logging.info(f"Diarization started for [{channel_name}/{file_name}]")

        import assemblyai as aai
        config = aai.TranscriptionConfig(speaker_labels=True)
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(file_path, config=config)

        if transcript is None:
            logging.error(f"Transcription returned None for file: [{file_path}]. This may be due to a '409 Conflict' error.")
            return

        utterances_dicts = [utterance_to_dict(utterance) for utterance in transcript.utterances]

        with open(transcript_file_path, 'w') as file:
            json.dump(utterances_dicts, file, indent=4)

        logging.info(f"Transcript for [{channel_name}/{file_name}] saved to [{channel_name}/{transcript_file_name}]")

    except Exception as e:
        logging.error(f"Error transcribing {file_path}: {e}")


def worker(api_key, file_paths):
    # Ensure this function and any function it calls are defined at the top level of the module.
    set_api_key(api_key)
    with ThreadPoolExecutor(max_workers=3) as executor:
        api_key_file_paths = [(api_key, file_path) for file_path in file_paths]
        list(executor.map(transcribe_and_save, api_key_file_paths))  # Force execution with list()


def main():
    load_dotenv()
    api_keys = os.environ.get('ASSEMBLY_AI_API_KEYS')
    if not api_keys:
        raise EnvironmentError("ASSEMBLY_AI_API_KEYS environment variable not found. Please set it before running the script.")
    api_keys = api_keys.split(',')

    data_path = YOUTUBE_VIDEO_DIRECTORY
    mp3_files = [os.path.join(root, file) for root, _, files in os.walk(data_path) for file in files if file.endswith(".mp3") and is_valid_filename(file)]
    if not mp3_files:
        logging.warning("No MP3 files found to transcribe.")
        return

    # Split files evenly among API keys
    files_per_key = len(mp3_files) // len(api_keys)
    file_chunks = [mp3_files[i:i + files_per_key] for i in range(0, len(mp3_files), files_per_key)]

    with ProcessPoolExecutor(max_workers=len(api_keys)) as executor:
        futures = [executor.submit(worker, api_key, file_chunks[i % len(file_chunks)]) for i, api_key in enumerate(api_keys)]
        for future in futures:
            future.result()  # Wait for all futures to complete, handling any exceptions.


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()  # Get the default logger
    logger.addFilter(No200HTTPFilter())  # Apply the No200HTTPFilter to the logger

    main()

