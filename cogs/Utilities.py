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
        asyncio.create_task(self.bot.db.execute('CREATE TABLE IF NOT EXISTS reaction_roles (message_id INTEGER, role_id INTEGER, emoji TEXT)'))

    @commands.command(usage="<title> <emote> <role id>; [emote] <role id>; ...", aliases=[])
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def reaction_roles(self, ctx:commands.Context, title:str, *, pairs:str):
        """
        Give roles based on reactions.
        """
        pairs = pairs.split(";")
        if not pairs:
            await ctx.send("You need to provide at least one emote role pair.")
            return

        pairs = [pair.strip().split() for pair in pairs]
        if not all(len(pair) == 2 for pair in pairs):
            await ctx.send("You need to provide emote role pairs in the format `emote role_id`, separated by semicolons.")
            return
        emote_role_pairs = []
        for emote, role in pairs:
            try:
                emoji = emote.strip() if emote.strip() in ''.join(UNICODE_EMOJI['en'].keys()) else self.bot.get_emoji(emote.strip())
                if emoji is None:
                    await ctx.send("Invalid emoji: {}. Please only use default emojis or emojis belonging to this guild.".format(emote.strip()))
                    return
                emote_role_pairs.append((emoji, ctx.guild.get_role(int(role.strip()))))
            except ValueError:
                await ctx.send("Invalid role ID: {}.".format(role))
                return

        embed = nextcord.Embed(title=title, description="\n".join(["{}: {}".format(emote, role) for emote, role in emote_role_pairs]))
        msg = await ctx.send(embed=embed)
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
