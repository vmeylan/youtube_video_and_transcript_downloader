#!/bin/bash

# create virtual environment
python -m venv venv

# activate virtual environment
source venv/bin/activate

# install packages from requirements.txt
pip install -r requirements.txt

# create a local .env file with the specified default values
cat <<EOL > .env
YOUTUBE_API_KEY=<Your_Youtube_API_Key>
ASSEMBLY_AI_API_KEYS=<Your_Assembly_AI_key>
EOL

# give user a notice
echo "A .env file has been created. Please update its values with your API key, channels, and playlists."
