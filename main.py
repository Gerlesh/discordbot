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


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()
        self.command_attrs = {'name': "help", 'usage': "<optional command>", 'aliases': ["commands", "q"],
                              'help': "Shows this help message.\nAdd a command to get information about it."}

    def get_bot_mapping(self) -> dict:
        """Retrieves the bot mapping passed to :meth:`send_bot_help`."""
        bot = self.context.bot
        mapping = {cog: cog.get_commands() for cog in bot.cogs.values()}
        mapping['General'] = [c for c in bot.commands if c.cog is None]
        return mapping

    async def send_bot_help(self, mapping:dict):
        copy = mapping.copy()
        for cog, coms in copy.items():
            for c in coms:
                try:
                    await c.can_run(self.context)
                except commands.CheckFailure:
                    mapping[cog].remove(c)
            if not mapping[cog]:
                mapping.pop(cog)

        embed = nextcord.Embed(title="Commands")
        cog = [cog for cog in mapping.keys() if isinstance(cog, str)][0]
        embed.add_field(name="**__" + (cog.qualified_name if hasattr(cog, "qualified_name") else cog) + "__**",
                        value=cog.description if (
                                hasattr(cog, 'description') and cog.description) else "Miscellaneous commands",
                        inline=False)

        for command in sorted(mapping[cog], key=lambda c: c.name):
            embed.add_field(name=command.name, value=command.help.split("\n")[0])

        view = None
        if len(mapping.keys()) > 1:
            view = nextcord.ui.View()
            view.add_item(menus.HelpMenu(mapping))

        await self.context.send(embed=embed, view=view)

    async def send_command_help(self, command:commands.Command):
        try:
            await command.can_run(self.context)
        except commands.CheckFailure:
            await self.send_bot_help(self.get_bot_mapping())
            return

        bot = self.context.bot
        embed = nextcord.Embed(title=command.name + " info",
                              description=command.help)

        embed.add_field(name="Aliases",
                        value=', '.join([await bot.get_prefix_(bot, self.context.message)
                                        + (command.parent.name + " " if command.parent else '')
                                        + alias for alias in [command.name] + sorted(command.aliases)]))
        embed.add_field(name="Usage", value=await self.context.bot.get_prefix_(bot, self.context.message)
                                        + (command.parent.name + " " if command.parent else '')
                                        + command.name + (" " + command.usage if command.usage else ""))

        await self.context.send(embed=embed)

    async def send_group_help(self, group:commands.Group):
        try:
            await group.can_run(self.context)
        except commands.CheckFailure:
            await self.send_bot_help(self.get_bot_mapping())
            return

        bot = self.context.bot
        embed = nextcord.Embed(title=group.name + " info",
                              description=group.help)

        embed.add_field(name="Aliases",
                        value=', '.join([await bot.get_prefix_(bot, self.context.message) + alias for alias in [group.name] + sorted(group.aliases)]))
        embed.add_field(name="Usage", value=await self.context.bot.get_prefix_(bot, self.context.message) + group.name + " " + group.usage)
        embed.add_field(name="Subcommands", value=', '.join(sorted([command.name for command in group.commands])))

        await self.context.send(embed=embed)

async def run():
    """
    Where the bot gets started.
    """

    config = config_load()
    db = await sql.connect(config["database"])
    await db.execute(
        'CREATE TABLE IF NOT EXISTS "prefixes" ("server_id" INTEGER PRIMARY KEY, "prefix" TEXT)'
    )

    bot = Bot(config=config, description=config['description'] if 'description' in config else None, db=db)

    bot.get_misc_commands()

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
            help_command=HelpCommand(),
            intents=nextcord.Intents.default()
        )

        self.config = kwargs.pop('config')

        self.db = kwargs.pop('db')

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

    async def get_prefix_(self, bot:commands.Bot, msg:nextcord.Message):
        """
        Returns the prefix to be used with the message (i.e. guild prefix)
        """

        async with self.db.execute('SELECT prefix FROM prefixes WHERE server_id=?', (msg.guild.id,)) as cur:
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
        if any([len(i.get_commands())>24 for i in self.cogs.values()]):
            raise OverflowError("Too many commands in cog (help command would not work).")

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

    async def on_message(self, message:nextcord.Message):
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

        if self._closed:
            return

        await self.http.close()
        self._closed = True

        await self.db.close()

        for voice in self.voice_clients:
            try:
                await voice.disconnect()
            except Exception:
                # if an error happens during disconnects, disregard it.
                pass

        if self.ws is not None and self.ws.open:
            await self.ws.close(code=1000)

        self._ready.clear()

    async def on_command_error(self, ctx:commands.Context, error:Exception):
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

        if isinstance(error, nextcord.errors.Forbidden):
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
            except nextcord.Forbidden:
                pass
            return

        if isinstance(error, commands.CheckFailure):
            return

        # ignore all other exception types, but print them to stderr
        print('\n\nIgnoring exception in command {}:'.format(ctx.command), file=sys.stderr)

        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_misc_commands(self):
        @self.command(usage='')
        @commands.is_owner()
        async def update(ctx:commands.Context):
            """
            Update the bot from the github page. Only usable by the owner of the bot.
            """
            await ctx.send("Restarting...")
            await ctx.bot.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    os.execvp("sh", ('sh', './update.sh'))
