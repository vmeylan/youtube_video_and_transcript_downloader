## YouTube Transcript and Video Downloader

### Description:
This script downloads transcripts of videos from given YouTube channels. Optionally, it can also download the videos.

### Setup:
1. Ensure you have Python 3.6 or newer installed.
2. Install the required packages: 
`pip install -r requirements.txt`

3. Set up a `.env` file with the following environment variables:
- `YOUTUBE_API_KEY`: Your YouTube Data API key.
- `YOUTUBE_CHANNELS`: Comma-separated list of YouTube channel names or IDs.
- `DOWNLOAD_VIDEO`: Set to `True` if you want to download videos along with transcripts. Default is `True`.

### Usage:
You can run the script in two ways:

1. **Using environment variables**:
Simply execute the script.
`python youtube_downloader.py`

2. **Using command-line arguments**:
`python youtube_downloader.py --api_key YOUR_YOUTUBE_API_KEY --channels CHANNEL_NAME_OR_ID [ANOTHER_CHANNEL_NAME_OR_ID ...]`


### Output:
Transcripts will be saved as `.txt` files in the `data` directory, organized by channel name. If `DOWNLOAD_VIDEO` is set to `True`, videos will also be downloaded to the respective channel directory.

### Additional Notes:
- The script processes channels and videos concurrently for efficiency using `asyncio`.
- The `DOWNLOAD_VIDEO` option is only available through the `.env` file.
- The script handles both channels specified by name or directly by ID.
