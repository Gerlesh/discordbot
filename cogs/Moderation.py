from datetime import timedelta

import nextcord
from nextcord.ext import commands
from pytimeparse.timeparse import timeparse

from cogs.utils import checks


class Moderation(commands.Cog):
    """
    Moderation commands.
    All of these commands have permsision requirements to be executed.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(usage='<user> [reason]', aliases=[])
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx:commands.Context, user:nextcord.Member, *, reason:str=None):
        """
        Kick a user from the server.
        Only users with kick permissions can use this command.
        """
        await user.kick(reason=reason)
        await ctx.send(user.name+" has been kicked from the server"+(" for "+reason if reason else "")+".") 

    @commands.command(usage='<user> [reason]', aliases=[])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx:commands.Context, user:nextcord.Member, *, reason:str=None):
        """
        Ban a user from the server.
        Only users with ban permissions can use this command.
        """
        await user.ban(reason=reason)
        await ctx.send(user.name+" has been banned from the server"+(" for "+reason if reason else "")+".")

    @commands.command(usage='<user> [reason]', aliases=[])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx:commands.Context, user:nextcord.User, *, reason:str=None):
        """
        Unban a user from the server by user id.
        Only users with ban permissions can use this command.
        """
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(user.name+" has been unbanned from the server"+(" for "+reason if reason else "")+".")

    @commands.command(usage='<user> <duration> [reason]', aliases=['timeout'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx:commands.Context, user:nextcord.Member, duration:timeparse, *, reason:str=None):
        """
        Mute a user in the server.
        Only users with timeout permissions can use this command.
        """
        if duration is None:
            await ctx.send("That is not a valid duration")
        await user.edit(timeout=timedelta(seconds=duration), reason=reason)
        await ctx.send(user.name+" has been muted"+(" for "+reason if reason else "")+".")

    @commands.command(usage='<user> [reason]', aliases=['untimeout'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx:commands.Context, user:nextcord.Member, *, reason:str=None):
        """
        Unmute a user before the timeout expires.
        Only users with the timeout permissions can use this command.
        """
        await user.edit(timeout=None, reason=reason)
        await ctx.send(user.name+" has been unmuted"+(" for "+reason if reason else "")+".")
        

def setup(bot):
    bot.add_cog(Moderation(bot))
