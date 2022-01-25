import nextcord
from nextcord.ext import commands


class Administration(commands.Cog):
    """
    Basic server administrating
    """

    def __init__(self, bot):
        self.bot = bot
        self.reactions = {'Gerlesh': '<:Gerlesh:898412274807603210>',
                          'Sukari': '<:Sukari:898412198186086431>',
                          'Aster': '<:Aster:898412009387864124>',
                          'Potato': '<:Potato:898412104149794826>',
                          'Solar': '<:Solar:898412341954232330>'}

    @commands.Cog.listener()
    async def on_message(self, msg:nextcord.Message):
        """
        Automatically add streamer reactions to stream announcements in stream announcements channel
        """
        if msg.channel.id == 895508695532830781 and msg.author.id == 375805687529209857 and "on Twitch" in msg.content:
            name = msg.content.split()[1]
            if name in self.reactions:
                await msg.add_reaction(self.reactions[name])


def setup(bot):
    bot.add_cog(Administration(bot))
