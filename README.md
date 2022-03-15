# Gerlesh's Discord Bot
A simple and easily expandable discord bot.

## Running the bot
To run the bot, clone this repo and create a folder called `secrets` in the bots main folder, copy your token,
and save it in a file called `discord_bot_token` in the folder you just made. Make sure the file does not have
an ending (like `.txt` or `.py`).

Install the bot's dependencies in a virtual environment using the commands:

```sh
// Linux/MacOS
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```
```bat
// Windows
python -m venv .venv
.venv/Scripts/activate.bat
pip install -r requirements.txt
```

If you are using a virtual environment, be sure to activate it before running these commands.
Then to run the bot, add the token as an environment variable:

```sh
// Linux/MacOS
export DISCORD_BOT_TOKEN=$(cat ./secrets/discord_bot_token)
python3 main.py
```
```bat
// Windows
set /P DISCORD_BOT_TOKEN=<.\\secrets\\discord_bot_token
python main.py
```
