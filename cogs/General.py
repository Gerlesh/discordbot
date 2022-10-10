import os
import sys
import subprocess

import nextcord
from nextcord.ext import commands
import git

from .utils import menus


class General(commands.Cog):
    """
    General bot commands.
    """
    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @nextcord.slash_command()
    async def update(self, interaction:nextcord.Interaction):
        """
        Update the bot from the github page.
        Only usable by the owner of the bot.
        """
        appinfo = await self.bot.application_info()
        if interaction.user.id != appinfo.owner.id:
            await interaction.send("Only the bot owner can run this command.", ephemeral=True)
            return
        await interaction.send("Updating...", ephemeral=True)
        repo = git.Repo(os.getcwd())
        origin = repo.remote(name='origin')
        origin.pull()
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        await self.bot.close()   # Restart update loop


def setup(bot):
    bot.add_cog(General(bot))
