# YouTube Transcript Downloader

This script fetches transcripts of videos from specified YouTube channels or playlists and saves them as .txt files. Optionally, it can also download the corresponding videos.

## Requirements

- A valid YouTube Data API key.
- Python packages: `asyncio`, `itertools`, `os`, `argparse`, `youtube_transcript_api`, `googleapiclient`, `dotenv`, and `pytube`.

## Setup

1. Clone this repository:
git clone [your-repository-link]
cd [your-repository-directory]

2. Run the setup.sh script to install the required Python packages and setup the .env file in the root directory.
3. Replace `'YOUR_YOUTUBE_API_KEY'` with your actual YouTube Data API key and adjust other parameters as needed.
4. Populate channels IDs in `YOUTUBE_CHANNELS` or playlists IDs `YOUTUBE_PLAYLISTS` separated by commas  

## Usage

To fetch transcripts and optionally download videos, run the following command:
`python script_name.py --api_key 'YOUR_YOUTUBE_API_KEY' --channels 'channel_name_1 channel_name_2 ...' --playlists 'playlist_id_1 playlist_id_2 ...'`


- `'YOUR_YOUTUBE_API_KEY'`: Replace this with your YouTube Data API key.
- `'channel_name_1 channel_name_2 ...'`: A space-separated list of YouTube channel names or IDs.
- `'playlist_id_1 playlist_id_2 ...'`: A space-separated list of YouTube playlist IDs.

Alternatively, if you've set up the `.env` file as instructed above, you can simply run: `python youtube_download.py`

This will use the API key and other parameters specified in the `.env` file.

## Note

- Transcripts are saved in a directory named `data`, with subdirectories for each channel or playlist. Each video's transcript is saved as a .txt file named using the video's title.
- The script uses the `youtube_transcript_api` to fetch transcripts. If a transcript is not available for a particular video, the script will skip that video and continue with the next.
- By setting the `DOWNLOAD_VIDEO` environment variable to `True`, the script will also download the videos corresponding to the transcripts. Videos are saved as .mp4 files in the same directories as the transcripts.

## Contributing

If you have suggestions or improvements, feel free to submit a pull request or open an issue.


