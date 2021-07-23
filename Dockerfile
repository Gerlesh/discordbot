FROM gerlesh/calibre-python:latest

RUN apt-get update -y && apt-get install git -y && git clone https://github.com/Gerlesh/discordbot.git && git pull origin master && mv /discordbot /app
WORKDIR /app
RUN chmod +x update.sh && pip3 install -r requirements.txt