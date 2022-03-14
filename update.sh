#!/bin/bash

git pull origin master
chmod +x update.sh
pip3 install -r requirements.txt
if python3 --version ; then
    python3 -u main.py
else
    python main.py
fi
