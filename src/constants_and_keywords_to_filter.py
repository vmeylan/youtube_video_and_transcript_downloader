# Note, the use of keywords List is an attempt at filtering YouTube videos by name content to reduce noise
from src.utils.utils import root_directory

AUTHORS = ['Robert Miller']
FIRMS = ['Flashbots']
KEYWORDS_TO_INCLUDE = ['MEV']

KEYWORDS_TO_INCLUDE += AUTHORS
KEYWORDS_TO_INCLUDE += FIRMS

KEYWORDS_TO_EXCLUDE = ['#shorts']

YOUTUBE_VIDEO_DIRECTORY = f"{root_directory()}/datasets/evaluation_data/diarized_youtube_content_2023-10-06/"
YOUTUBE_CHANNELS_FILE = f"{root_directory()}/data/youtube_channel_handles.txt"
YOUTUBE_VIDEOS_CSV_FILE_PATH = f"{root_directory()}/data/links/youtube/youtube_videos.csv"
MAPPING_FILE_PATH = f"{root_directory()}/data/links/youtube/youtube_video_mapping.csv"
