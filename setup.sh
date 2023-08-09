#!/bin/bash

# create virtual environment
python -m venv env

# activate virtual environment
source env/bin/activate

# install packages from requirements.txt
pip install -r requirements.txt

# create a local .env file with the specified default values
cat <<EOL > .env
YOUTUBE_API_KEY=<Your_Youtube_API_Key>
YOUTUBE_CHANNELS=<Channel1>,<Channel2>,...
YOUTUBE_PLAYLISTS=<Playlist1>,<Playlist2>,...
DOWNLOAD_VIDEO=True
EOL

# give user a notice
echo "A .env file has been created. Please update its values with your API key, channels, and playlists."

# deactivate virtual environment
deactivate
