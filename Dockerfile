FROM gerlesh/calibre-python:latest

RUN mkdir /app
WORKDIR /app
RUN apt-get update -y && apt-get install git -y && git clone https://github.com/Gerlesh/discordbot.git

RUN pip3 install -r requirements.txt