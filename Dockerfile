FROM gerlesh/calibre-python:latest

RUN apt-get update -y && apt-get install git -y && git clone https://github.com/Gerlesh/discordbot.git && mv /discordbot /app
WORKDIR /app
RUN pip3 install -r requirements.txt