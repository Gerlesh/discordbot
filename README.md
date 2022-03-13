# Gerlesh's Discord Bot
A simple and easily expandable discord bot.

## Running the bot
There are two easy free ways to run the bot, Through Docker and directly on your system. For both of these methods, make sure you get your bot token from the [Discord Developer Portal](https://discord.com/developers/applications). If you're not sure how, [here's a useful tutorial](https://www.writebots.com/discord-bot-token/).

Create a folder called `secrets` in the bots main folder, copy your token, and save it in a file called `discord_bot_token` in the folder you just made. Make sure the file does not have an ending (like `.txt` or `.py`).

### Docker Container
Docker is a useful container system that allows you to run programs in isolation from the rest of your system. I like this system because you can set the bot to automatically run on startup and in the background, so you never have to worry about it.

To get started, install [Docker for your system](https://docs.docker.com/engine/install/). Make sure you follow all the steps, including any post-installation that is needed for your system.

Then, starting the bot is as simple as opening a Terminal or Command Line and typing `docker-compose build && docker-compose up`. Make sure the terminal is open to the bot's folder before running this command.

To make the bot automatically restart, enter `docker update --restart unless-stopped discord-bot` into the terminal window, and make sure Docker is configured to run on startup!

> **NOTE**: THIS METHOD WILL ALWAYS UPDATE FROM GITHUB. IT WILL NOT UPDATE WITH LOCAL CHANGES.

If you are a more advanced user and would like to customise the bot's functionality for your use, you can modify line 8 in the `Dockerfile` to point to your own repo, and the container will clone from there instead of this one.

### Regular
If you do not want to run the bot in a Docker container, whether for more fine-tuned control or just for convenience, you can directly run the update.sh file itself.