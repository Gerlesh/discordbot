from datetime import timedelta

import nextcord
from nextcord.ext import commands
from pytimeparse.timeparse import timeparse

class Moderation(commands.Cog):
    """
    Moderation commands.
    All of these commands have permsision requirements to be executed.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @nextcord.slash_command()
    async def kick(self, interaction:nextcord.Interaction, user:nextcord.Member, reason:str=nextcord.SlashOption(required=False)):
        """
        Kick a user from the server.
        Only users with kick permissions can use this command.
        """
        if not interaction.permissions.kick_members:
            await interaction.send("Only users with the `Kick Members` permission can use this command.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.kick_members:
            await interaction.send("I need the `Kick Members` permission to use this command.", ephemeral=True)
            return
        try:
            await user.kick(reason=reason)
        except nextcord.Forbidden:
            await interaction.send("I do not have sufficient permissions to kick "+user.name+" from the server.", ephemeral=True)
        else:
            await interaction.send(user.name+" has been kicked from the server"+(" for "+reason if reason else "")+".", ephemeral=True)

    @nextcord.slash_command()
    async def ban(self, interaction:nextcord.Interaction, user:nextcord.Member, reason:str=nextcord.SlashOption(required=False)):
        """
        Ban a user from the server.
        Only users with ban permissions can use this command.
        """
        if not interaction.permissions.ban_members:
            await interaction.send("Only users with the `Ban Members` permission can use this command.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.send("I need the `Ban Members` permission to use this command.", ephemeral=True)
            return
        try:
            await user.ban(reason=reason)
        except nextcord.Forbidden:
            await interaction.send("I do not have sufficient permissions to ban "+user.name+" from the server.", ephemeral=True)
        else:
            await interaction.send(user.name+" has been banned from the server"+(" for "+reason if reason else "")+".", ephemeral=True)

    @nextcord.slash_command()
    async def unban(self, interaction:nextcord.Interaction, user:nextcord.User, reason:str=nextcord.SlashOption(required=False)):
        """
        Unban a user from the server by user id.
        Only users with ban permissions can use this command.
        """
        if not interaction.permissions.ban_members:
            await interaction.send("Only users with the `Ban Members` permission can use this command.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.ban_members:
            await interaction.send("I need the `Ban Members` permission to use this command.", ephemeral=True)
            return
        try:
            await interaction.guild.unban(user, reason=reason)
        except nextcord.Forbidden:
            await interaction.send("I do not have sufficient permissions to unban "+user.name+" from the server.", ephemeral=True)
        else:
            await interaction.send(user.name+" has been unbanned from the server"+(" for "+reason if reason else "")+".", ephemeral=True)

    @nextcord.slash_command()
    async def mute(self, interaction:nextcord.Interaction, user:nextcord.Member, duration:str, reason:str=nextcord.SlashOption(required=False)):
        """
        Mute a user in the server.
        Only users with timeout permissions can use this command.
        """
        if not interaction.permissions.moderate_members:
            await interaction.send("Only users with the `Timeout Members` permission can use this command.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.send("I need the `Timeout Members` permission to use this command.", ephemeral=True)
            return
        duration = timeparse(duration)
        if duration is None:
            await interaction.send("That is not a valid duration.", ephemeral=True)
            return
        try:
            await user.edit(timeout=timedelta(seconds=duration), reason=reason)
        except nextcord.Forbidden:
            await interaction.send("I do not have sufficient permissions to mute "+user.name+".", ephemeral=True)
        else:
            await interaction.send(user.name+" has been muted"+(" for "+reason if reason else "")+".", ephemeral=True)

    @nextcord.slash_command()
    async def unmute(self, interaction:nextcord.Interaction, user:nextcord.Member, reason:str=nextcord.SlashOption(required=False)):
        """
        Unmute a user before the timeout expires.
        Only users with the timeout permissions can use this command.
        """
        if not interaction.permissions.moderate_members:
            await interaction.send("Only users with the `Timeout Members` permission can use this command.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.send("I need the `Timeout Members` permission to use this command.", ephemeral=True)
            return
        await user.edit(timeout=None, reason=reason)
        await interaction.send(user.name+" has been unmuted"+(" for "+reason if reason else "")+".", ephemeral=True)
        

def setup(bot):
    bot.add_cog(Moderation(bot))
