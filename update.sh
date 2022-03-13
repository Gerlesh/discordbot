#!/bin/bash

git pull origin master
chmod +x update.sh
pip3 install -r requirements.txt
if python3 ; then
    export DISCORD_BOT_TOKEN=./secrets/discord_bot_token
    python3 -u main.py
else
    set DISCORD_BOT_TOKEN=secrets\\discord_bot_token
    python main.py
fi
