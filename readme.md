# YouTube Transcript Downloader

This script allows you to download transcripts of YouTube videos from specified channels. The transcripts are saved as `.txt` files in the `data` directory. You can provide YouTube channel names or IDs and your YouTube Data API key either via command line arguments or a `.env` file.

## Requirements

- Python 3.6 or higher
- Install dependencies from `requirements.txt` using `pip install -r requirements.txt`

## Usage

1. Clone the repository or download the script.

2. Create a `.env` file in the same directory as the script and add the following variables:

YOUTUBE_API_KEY=your_youtube_data_api_key
YOUTUBE_CHANNELS=channel_name_1,channel_name_2,channel_name_3

Replace `your_youtube_data_api_key` with your actual YouTube Data API key and `channel_name_1,channel_name_2,channel_name_3` with the YouTube channel names or IDs you want to fetch transcripts from. You can add more channels by separating them with commas.

3. Run the script with the following command:

python youtube_transcript_downloader.py

You can also provide the API key and channel names or IDs via command line arguments:

python youtube_transcript_downloader.py --api_key your_youtube_data_api_key --channels channel_name_1 channel_name_2 channel_name_3

Replace `your_youtube_data_api_key` with your actual YouTube Data API key and `channel_name_1 channel_name_2 channel_name_3` with the YouTube channel names or IDs you want to fetch transcripts from.

4. The script will create a `data` directory and save the transcripts as `.txt` files in subdirectories named after the channels.

## Notes

- The script may take some time to download transcripts, depending on the number of channels and videos.

- If a video does not have a transcript available, the script will log the information and skip that video.
