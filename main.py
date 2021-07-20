#!./env/Scripts/python.exe

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
import discord
from discord.ext import commands


def config_load():
    with open(os.path.join("data", "config.json"), 'r', encoding='utf-8-sig') as f:
        return json.load(f)


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.command_attrs = {'name': "help", 'usage': "<optional command>", 'aliases': ["commands", "q"],
                              'help': "Shows this help message.\nAdd a command to get information about it."}

    def get_bot_mapping(self):
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""
        bot = self.context.bot
        mapping = {
            cog: list(dict.fromkeys(cog.get_commands()))
            for cog in bot.cogs.values()
        }
        mapping["Other"] = list(dict.fromkeys([c for c in bot.all_commands.values() if c.cog is None]))
        return mapping

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Commands")
        for cog in mapping.keys():
            embed.add_field(name="**__" + (cog.qualified_name if hasattr(cog, "qualified_name") else cog) + "__**",
                            value=cog.description if (hasattr(cog, 'description') and cog.description) else "No Description", inline=False)

            for command in mapping[cog]:
                embed.add_field(name=command.name, value=command.help.split("\n")[0])

        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=command.name + " info",
                              description=command.help)

        embed.add_field(name="Aliases",
                        value=', '.join([self.clean_prefix + alias for alias in [command.name] + command.aliases]))
        embed.add_field(name="Usage", value=self.clean_prefix + command.name + " " + command.usage)
        await self.context.send(embed=embed)


async def run():
    """
    Where the bot gets started.
    """

    config = config_load()

    bot = Bot(config=config, description=config['description'] if 'description' in config else None)

    async with sql.connect(config['database']) as db:
        await db.execute(
            'CREATE TABLE IF NOT EXISTS "prefixes" ("server_id" INTEGER PRIMARY KEY, "prefix" TEXT)'
        )

    try:
        with open(os.getenv('DISCORD_BOT_TOKEN'), 'r') as f:
            await bot.start(f.read())
    except KeyboardInterrupt:
        await bot.logout()


class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix_,
            description=kwargs.pop('description'),
            help_command=HelpCommand()
        )

        self.config = kwargs.pop('config')

        self.start_time = None
        self.app_info = None

        self.loop.create_task(self.track_start())
        self.loop.create_task(self.load_all_extensions())

    async def track_start(self):
        """
        Waits for the bot to connect to discord and then records the time.
        """

        await self.wait_until_ready()
        self.start_time = datetime.datetime.utcnow()

    async def get_prefix_(self, bot, msg):
        """
        Returns the prefix to be used with the message (i.e. guild prefix)
        """

        async with sql.connect(self.config["database"]) as db:
            async with db.execute('SELECT prefix FROM prefixes WHERE server_id=?', (msg.guild.id,)) as cur:
                prefix = await cur.fetchone()

        return prefix if prefix is not None else '-'

    async def load_all_extensions(self):
        """
        Attempts to load all .py files in /cogs/ as cog extensions
        """

        await self.wait_until_ready()
        await asyncio.sleep(1)  # ensure that on_ready has completed and finished printing
        cogs = [x.stem for x in Path('cogs').glob('*.py')]
        for extension in cogs:
            try:
                self.load_extension(f'cogs.{extension}')
                print(f'loaded {extension}')
            except Exception as e:
                error = f'{extension}\n {type(e).__name__} : {e}'
                print(f'failed to load extension {error}')
            print('-' * 10)

    async def on_ready(self):
        """
        This event is called every time the bot connects or resumes connection.
        """

        print('-' * 10)
        self.app_info = await self.application_info()
        print(f'Logged in as: {self.user.name}\n'
              f'Using discord.py version: {discord.__version__}\n'
              f'Owner: {self.app_info.owner}\n'
              f'Time: {self.start_time}')
        print('-' * 10)

    async def on_message(self, message):
        """
        This event triggers on every message received by the bot to process commands.
        """

        if message.author.bot:
            return  # ignore all bots
        await self.process_commands(message)

    async def close(self):
        """
        Closes the connection to Discord and any database files.
        """

        if self._closed:
            return

        await self.http.close()
        self._closed = True

        for voice in self.voice_clients:
            try:
                await voice.disconnect()
            except Exception:
                # if an error happens during disconnects, disregard it.
                pass

        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)

        self._ready.clear()

    async def on_command_error(self, ctx, error):
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
                fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            _message = 'I need the **{}** permission(s) to run this command.'.format(fmt)
            await ctx.send(_message)
            return

        if isinstance(error, discord.errors.Forbidden):
            print("Forbidden action in", ctx.command.name)
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
                fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
            else:
                fmt = ' and '.join(missing)
            _message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
            await ctx.send(_message)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You are missing an argument. Usage: `"
                           + await self.get_prefix_(self, ctx.message) + ctx.command.name + ctx.command.usage + '`')
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("That is not a valid way to use the command. Use `"
                           + await self.get_prefix_(self, ctx.message) + "help" + ctx.command.name + "` for help.")
            return

        if isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send('This command cannot be used in direct messages.')
            except discord.Forbidden:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            return

        # ignore all other exception types, but print them to stderr
        print('\n\nIgnoring exception in command {}:'.format(ctx.command), file=sys.stderr)

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
