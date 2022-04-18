#!.venv/bin/python3.9

import asyncio
import datetime
import json
import logging
import math
import os
import sys
import traceback
from pathlib import Path

import aiosqlite as sql
import nextcord
from nextcord.ext import commands

from cogs.utils import menus


def config_load() -> dict:
    with open(os.path.join("data", "config.json"), 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def run(loop: asyncio.AbstractEventLoop):
    """
    Where the bot gets started.
    """

    config = config_load()

    bot = Bot(config=config,
              description=config['description'] if 'description' in config else None)

    try:
        loop.run_until_complete(bot.start(os.getenv('DISCORD_BOT_TOKEN')))
    except KeyboardInterrupt:
        loop.run_until_complete(bot.close())
        sys.exit()


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix_,
            description=kwargs.pop('description'),
            help_command=None,
            intents=nextcord.Intents.all()
        )

        self.config = kwargs.pop('config')

        self.start_time = None
        self.app_info = None
        self.db = None

        self.loop.create_task(self.db_connect())
        self.loop.create_task(self.track_start())
        self.loop.create_task(self.load_all_extensions())

    async def db_connect(self):
        self.db = await sql.connect(self.config["database"])
        await self.db.execute(
            'CREATE TABLE IF NOT EXISTS "guilds" ("guild_id" INTEGER PRIMARY KEY, "prefix" TEXT, "starboard" INTEGER, "star_min" INTEGER, CHECK(("starboard" IS NOT NULL AND "star_min" IS NOT NULL) OR ("starboard" IS NULL AND "star_min" IS NULL)))'
        )

    async def track_start(self):
        """
        Waits for the bot to connect to discord and then records the time.
        """

        await self.wait_until_ready()
        self.start_time = datetime.datetime.utcnow()

    async def get_prefix_(self, bot: commands.Bot, msg: nextcord.Message):
        """
        Returns the prefix to be used with the message (i.e. guild prefix)
        Default: -
        """

        cursor = await self.db.execute('SELECT prefix FROM guilds WHERE guild_id=?', (msg.guild.id,))
        prefix = await cursor.fetchone()

        return prefix[0] if prefix and prefix[0] else '-'

    async def load_all_extensions(self):
        """
        Attempts to load all .py files in /cogs/ as cog extensions
        """

        await self.wait_until_ready()
        # ensure that on_ready has completed and finished printing
        await asyncio.sleep(1)
        cogs = [x.stem for x in Path('cogs').glob('*.py')]
        for extension in cogs:
            try:
                self.load_extension(f'cogs.{extension}')
                print(f'loaded {extension}')
            except Exception as e:
                error = f'{extension}\n {type(e).__name__} : {e}'
                print(f'failed to load extension {error}')
            print('-' * 10)
        if any([len(i.get_commands()) > 24 for i in self.cogs.values()]):
            raise OverflowError(
                "Too many commands in cog (help command would not work).")

    async def on_ready(self):
        """
        This event is called every time the bot connects or resumes connection.
        """

        print('-' * 10)
        self.app_info = await self.application_info()
        print(f'Logged in as: {self.user.name}\n'
              f'Using nextcord version: {nextcord.__version__}\n'
              f'Owner: {self.app_info.owner}\n'
              f'Time: {self.start_time}')
        print('-' * 10)

    async def on_message(self, message: nextcord.Message):
        """
        This event triggers on every message received by the bot to process commands.
        """

        if message.author.bot:
            return  # ignore all bots
        await self.process_commands(message)

    async def close(self):
        """
        Closes the connection to discord and any database files.
        """

        await self.db.close()

        await super().close()
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """
        Handles all errors in commands.
        """

        # if command has local error handler, return
        if hasattr(ctx.command, 'on_error'):
            return

        # get the original exception
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.BotMissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server')
                           .title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = '{}, and {}'.format(
                    "**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            _message = 'I need the **{}** permission(s) to run this command.'.format(
                fmt)
            await ctx.send(_message)
            return

        if isinstance(error, nextcord.errors.Forbidden):
            print("Forbidden action in ", ctx.command.name)
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send('This command has been disabled.')
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("This command is on cooldown, please retry in {}s."
                           .format(math.ceil(error.retry_after)))
            return

        if isinstance(error, commands.MissingRole):
            await ctx.send("You can't use that command.")
            return

        if isinstance(error, commands.MissingPermissions):
            missing = [perm.replace('_', ' ').replace('guild', 'server')
                           .title() for perm in error.missing_perms]
            if len(missing) > 2:
                fmt = '{}, and {}'.format(
                    "**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            _message = 'You need the **{}** permission(s) to use this command.'.format(
                fmt)
            await ctx.send(_message)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You are missing an argument. Usage: `"
                           + await self.get_prefix_(self, ctx.message) + ctx.command.name + ' ' + ctx.command.usage + '`')
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("That is not a valid way to use the command. Use `"
                           + await self.get_prefix_(self, ctx.message) + "help " + ctx.command.name + "` for help.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send('This command cannot be used in direct messages.')
            except nextcord.Forbidden:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            return

        # ignore all other exception types, but print them to stderr
        print('\n\nIgnoring exception in command {}:'.format(
            ctx.command), file=sys.stderr)

        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr)


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    run(loop)
    os.execvp("sh", ("sh", os.path.join(os.getcwd(), 'update.sh')))
