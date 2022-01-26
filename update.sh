#!/bin/bash

git pull origin ASGbot
chmod +x update.sh
pip3 install -r requirements.txt
python3 -u main.py