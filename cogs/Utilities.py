import asyncio

import nextcord
from nextcord.ext import commands
from nextcord.utils import get
import aiosqlite
from emoji import UNICODE_EMOJI

class Utilities(commands.Cog):
    """
    Basic server utilities.
    """
    def __init__(self, bot):
        self.bot = bot
        self.emotes = ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.db.execute('CREATE TABLE IF NOT EXISTS reaction_roles (message_id INTEGER, role_id INTEGER, emoji TEXT)')

    @nextcord.slash_command()
    async def reaction_roles(self, interaction:nextcord.Interaction, title:str,
        role0:nextcord.Role,
		role1:nextcord.Role=nextcord.SlashOption(required=False),
		role2:nextcord.Role=nextcord.SlashOption(required=False),
		role3:nextcord.Role=nextcord.SlashOption(required=False),
		role4:nextcord.Role=nextcord.SlashOption(required=False),
		role5:nextcord.Role=nextcord.SlashOption(required=False),
		role6:nextcord.Role=nextcord.SlashOption(required=False),
		role7:nextcord.Role=nextcord.SlashOption(required=False),
		role8:nextcord.Role=nextcord.SlashOption(required=False),
		role9:nextcord.Role=nextcord.SlashOption(required=False)
    ):
        """
        Give roles based on reactions.
        """
        if isinstance(interaction.channel, nextcord.PartialMessageable):
            await interaction.send("This command can only be used in guilds.", ephemeral=True)
            return
        if not interaction.permissions.manage_roles:
            await interaction.send("Only users with the `Manage Roles` permission can use this command.", ephemeral=True)
            return
        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.send("I need the `Manage Roles` permission to use this command.", ephemeral=True)
            return

        roles = (role0, role1, role2, role3, role4, role5, role6, role7, role8, role9)
        for role in roles:
            if role is not None and role > interaction.guild.me.top_role:
                await interaction.send("I do not have sufficient permissions to give "+role.name+".", ephemeral=True)
                return

        emote_role_pairs = [(self.emotes[i], roles[i]) for i in range(10) if roles[i] is not None]

        embed = nextcord.Embed(title=title, description="\n".join(["{}: {}".format(emote, role) for emote, role in emote_role_pairs]))
        await interaction.send(embed=embed)
        msg = await interaction.original_message()
        for emote, role in emote_role_pairs:
            await msg.add_reaction(emote)

        await self.bot.db.executemany('INSERT INTO reaction_roles VALUES (?, ?, ?)', [(msg.id, role.id, str(emote)) for emote, role in emote_role_pairs])
        await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        Give roles based on reactions to messages with reaction roles.
        """
        if payload.user_id == self.bot.user.id:
            return

        cursor = await self.bot.db.execute('SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?', (payload.message_id, payload.emoji.name))
        role_id = await cursor.fetchone()

        if role_id:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id[0])
            if role:
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """
        Remove roles based on reactions to messages with reaction roles.
        """
        if payload.user_id == self.bot.user.id:
            return

        cursor = await self.bot.db.execute('SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?', (payload.message_id, payload.emoji.name))
        role_id = await cursor.fetchone()

        if role_id:
            guild = self.bot.get_guild(payload.guild_id)
            role = guild.get_role(role_id[0])
            if role:
                await get(guild.members, id=payload.user_id).remove_roles(role)

def setup(bot):
    bot.add_cog(Utilities(bot))
