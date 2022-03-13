#!/bin/bash

git pull origin ASGbot
chmod +x update.sh
pip3 install -r requirements.txt
export DISCORD_BOT_TOKEN=./secrets/discord_bot_token
if python3 ; then
    python3 -u main.py
else
    python main.py
fi
