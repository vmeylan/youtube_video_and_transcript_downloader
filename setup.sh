#!/bin/bash

# create virtual environment
python -m venv env

# activate virtual environment
source env/bin/activate

# install packages from requirements.txt
pip install -r requirements.txt

# deactivate virtual environment
deactivate
