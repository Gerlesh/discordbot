import nextcord
from nextcord.ext import commands
from setuptools import Command

from .utils import menus


class General(commands.Cog):
    """
    General bot commands.
    """
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command(usage="[command]", aliases=["commands", "q"])
    async def help(self, ctx, command:str=None, subcommand:str=None):
        """
        Shows this help message.
        Add a command to get information about it.
        """
        if command is None: # General help
            mapping = {cog: cog.get_commands() for cog in self.bot.cogs.values()}
            copy = {cog: commands[:] for cog, commands in mapping.items()}

            # Only show commands that the invoker can use
            for cog, cmds in copy.items():
                for c in cmds:
                    try:
                        await c.can_run(ctx)
                    except commands.CheckFailure:
                        mapping[cog].remove(c)
                if not mapping[cog]:
                    mapping.pop(cog)

            # Default cog commands embed
            embed = nextcord.Embed(title="Commands")
            cog = self
            embed.add_field(name="**__" + cog.qualified_name + "__**",
                            value=cog.description,
                            inline=False)

            for command in sorted(mapping[cog], key=lambda c: c.name):
                embed.add_field(name=command.name, value=command.help.split("\n")[0])

            # Add selection menu to see commands from other cogs
            view = None
            if len(mapping.keys()) > 1:
                view = nextcord.ui.View()
                view.add_item(menus.HelpMenu(self.bot, mapping))

            await ctx.send(embed=embed, view=view)
            return
        
        cmd = self.bot.get_command(command) # Command help
        
        if cmd is None:
            await ctx.send("That's not a valid command!")
            return

        if isinstance(cmd, commands.Group) and subcommand is None:
            try:
                await cmd.can_run(ctx)
            except commands.CheckFailure:
                await ctx.send("That's not a valid command!")
                return

            embed = nextcord.Embed(title=cmd.name + " info",
                                description=cmd.help)
            
            embed.add_field(name="Aliases",
                            value=', '.join([await self.bot.get_prefix_(self.bot, ctx.message) + alias for alias in [cmd.name] + sorted(cmd.aliases)]))
            embed.add_field(name="Usage", value=await self.bot.get_prefix_(self.bot, ctx.message) + cmd.name + " " + cmd.usage)
            embed.add_field(name="Subcommands", value=', '.join(sorted([command.name for command in cmd.commands])))

            await ctx.send(embed=embed)
        else:
            if subcommand is not None:
                cmd = self.bot.get_command(command+" "+subcommand)
                if cmd is None:
                    await ctx.send("That's not a valid command!")

            try:
                await cmd.can_run(ctx)
            except commands.CheckFailure:
                await ctx.send("That's not a valid command!")
                return


            embed = nextcord.Embed(title=cmd.name + " info",
                                description=cmd.help)

            embed.add_field(name="Aliases",
                            value=', '.join([await self.bot.get_prefix_(self.bot, ctx.message)
                                            + (cmd.parent.name + " " if cmd.parent else '')
                                            + alias for alias in [cmd.name] + sorted(cmd.aliases)]))
            embed.add_field(name="Usage", value=await self.bot.get_prefix_(self.bot, ctx.message)
                                            + (cmd.parent.name + " " if cmd.parent else '')
                                            + cmd.name + (" " + cmd.usage if cmd.usage else ""))

            await ctx.send(embed=embed)

    @commands.command(usage='', aliases=["code","source"])
    async def github(self, ctx:commands.Context):
        """
        Get a link to the bot's github page.
        See how the bot and its commands work
        """
        await ctx.send("The source code for this bot can be found on github at https://github.com/Gerlesh/discordbot.\nIt is maintained and run by Gerlesh#4108")

    @commands.command(usage='')
    @commands.is_owner()
    async def update(self, ctx:commands.Context):
        """
        Update the bot from the github page.
        Only usable by the owner of the bot.
        """
        await ctx.send("Restarting...")
        await ctx.bot.close()   # Restart update loop


def setup(bot):
    bot.add_cog(General(bot))
