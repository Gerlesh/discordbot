FROM gerlesh/calibre-python:latest

RUN mkdir /app
WORKDIR /app
RUN apt-get update -y && apt-get install git -y && git clone https://github.com/Gerlesh/discordbot.git && git init \
    && git pull origin master && chmod +x update.sh && pip3 install -r requirements.txt