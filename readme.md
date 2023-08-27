# YouTube Transcript Downloader

This script fetches transcripts of videos from specified YouTube channels or playlists and saves them as .txt files. Optionally, it can also download the corresponding videos. 

It can fetch private videos if access is granted to Google Service Accounts on a private video by private video basis. Unfortunately, there is no direct way of scaling the download process to private playlists as of the writing date.

## Requirements

- A valid YouTube Data API key.
- Optional: Google service account to download private videos
- Python packages: `asyncio`, `itertools`, `os`, `argparse`, `youtube_transcript_api`, `googleapiclient`, `dotenv`, and `pytube`.

## Setup

1. Clone this repository:
   - `git clone https://github.com/vmeylan/youtube_video_and_transcript_downloader.git`
   - `cd youtube_video_and_transcript_downloader`

2. Run the setup.sh script to install the required Python packages and setup the .env file in the root directory. `./setup.sh`
3. Replace 'YOUR_YOUTUBE_API_KEY' with your actual YouTube Data API key and adjust other parameters as needed.
4. Populate channels IDs in `YOUTUBE_CHANNELS` or playlists IDs `YOUTUBE_PLAYLISTS` separated by commas. 

## [Optional] Setting Up Google Service Account for Accessing Private Videos
To use the Google Service Account for downloading private YouTube videos, you'll need to grant the Service Account email access to each private video individually. As of now, there's no direct way to download private playlists or whole private channels using this method.

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Navigate to `IAM & Admin` > `Service accounts`, then click on `Create Service Account`.
4. Fill in the details and click `Create`.
5. In the `Service account permissions` section, you will be prompted to grant this service account access to specific roles. To work with the YouTube Data API, you would generally grant it the role of "Viewer". This allows the account to view, but not modify, most of the resources associated with the account.
 
    a. Click on the Select a role dropdown.

    b. Navigate to `YouTube Data API v3` > `YouTube Data API Viewer`.

    c. Click `Continue` to proceed.
6. Click `Continue` and then `Done`.
7. In the list of service accounts, find the one you just created and click on the three dots under `Actions` > `Manage keys`.
8. Click `Add key` and choose `JSON`. This will download a JSON file which is your service account credentials.
9. Store this JSON file safely and note the path. This path will be used as the `SERVICE_ACCOUNT_FILE` in the `.env` file.

### To grant your service account access to a private video:

1. Go to YouTube Studio.
2. Click on "Videos" on the left sidebar.
3. Select the private video you want to share.
4. Under the "Visibility" settings, you'll see an option to share the video with specific email addresses if it's set to "Private".
5. Add the service account's email address (you can find this in the Google Cloud Console under your service account details).
6. Save or confirm the changes.

7. Remember, you'll need to repeat the steps for each private video you wish to download.

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


