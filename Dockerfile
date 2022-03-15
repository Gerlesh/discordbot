FROM alpine:latest

RUN apk update && apk upgrade && \
    apk add --no-cache bash git openssh && \
    apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python && \
    python3 -m ensurepip && \
    pip3 install --no-cache --upgrade pip setuptools && \
    git clone https://github.com/Gerlesh/discordbot.git && \
    mv /discordbot /app
WORKDIR /app
RUN git switch ASGbot && chmod +x update.sh && pip3 install -r requirements.txt && export DISCORD_BOT_TOKEN=$(cat ./secrets/discord_bot_token)
