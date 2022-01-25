FROM python:3

RUN apt-get update -y && apt-get install git -y && git clone https://github.com/Gerlesh/discordbot.git && \
    mv /discordbot /app
WORKDIR /app
RUN git pull origin master && chmod +x update.sh && pip3 install -r requirements.txt
