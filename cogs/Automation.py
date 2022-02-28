import nextcord
from nextcord.ext import commands

class Automation(commands.Cog):
    """
    Basic server administrating
    """

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.reactions = {'Gerlesh': '<:Gerlesh:898412274807603210>',
                          'Sukari': '<:Sukari:898412198186086431>',
                          'Aster': '<:Aster:898412009387864124>',
                          'Potato': '<:Potato:898412104149794826>',
                          'Solar': '<:Solar:898412341954232330>',
                          'Goodnight': '<:Goodnight:944709667110678588>'}

    @commands.Cog.listener()
    async def on_message(self, msg:nextcord.Message):
        """
        Automatically add streamer reactions to stream announcements in stream announcements channel
        """
        if msg.channel.id == 895508695532830781 and msg.author.id == 375805687529209857 and "on Twitch" in msg.content:
            name = msg.content.split()[1]
            if name in self.reactions:
                await msg.add_reaction(self.reactions[name])
                await msg.publish()
    
    @commands.Cog.listener()
    async def on_member_join(self, member:nextcord.Member):
        """
        Automatically assign the ASG Viewers role to new members and update viewer count channel
        """
        if member.guild.id == 891583482415960074:
            await member.add_roles(nextcord.utils.get(member.guild.roles, id=895498674656911421), reason="New viewer pog")
            viewer_count = len(member.guild.get_role(895498674656911421).members)
            channel = self.bot.get_channel(947906376338898984)
            await channel.edit(name="Viewer Count: "+str(viewer_count))

    @commands.Cog.listener()
    async def on_member_remove(self, member:nextcord.Member):
        """
        Automatically update viewer count channel when someone leaves the guild
        """
        if member.guild.id == 891583482415960074:
            viewer_count = len(member.guild.get_role(895498674656911421).members)
            channel = self.bot.get_channel(947906376338898984)
            await channel.edit(name="Viewer Count: "+str(viewer_count))

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Automatically update viewer count channel when bot reconnects
        """
        viewer_count = len(self.bot.get_guild(891583482415960074).get_role(895498674656911421).members)
        channel = self.bot.get_channel(947906376338898984)
        await channel.edit(name="Viewer Count: "+str(viewer_count))

def setup(bot:commands.Bot):
    bot.add_cog(Automation(bot))
