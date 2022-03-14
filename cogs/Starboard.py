import random

import nextcord
from nextcord.ext import commands

class Starboard(commands.Cog):
    """
    Starboard functionality.
    React to a message with a ⭐ to vote for starboard.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(bot.db.execute(
            'CREATE TABLE IF NOT EXISTS "starboard" ("message_id" INTEGER PRIMARY KEY, "guild_id" INTEGER NOT NULL, "channel_id" INTEGER NOT NULL, "star_count" INTEGER NOT NULL, "starboard_id" INTEGER)'))
        bot.loop.create_task(bot.db.execute(
            'CREATE TABLE IF NOT EXISTS "starboard_config" ("guild_id" INTEGER PRIMARY KEY, "star_min" INTEGER NOT NULL, "channel" INTEGER NOT NULL)'))


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent): 
        """
        Update starboard score when a reaction is added.
        """
        cursor = await self.bot.db.execute('SELECT * FROM "starboard_config" WHERE "guild_id"=?', (payload.guild_id,))
        if await cursor.fetchone() is None: 
            return

        if payload.emoji.name == '⭐':
            reaction_channel = self.bot.get_channel(payload.channel_id)
            message = await reaction_channel.fetch_message(payload.message_id)
            try:
                count = list(filter(lambda r: r.emoji == '⭐', message.reactions))[0].count
            except IndexError:
                count = 0

            cursor = await self.bot.db.execute('INSERT INTO "starboard" ("message_id", "guild_id", "channel_id", "star_count") VALUES (?,?,?,?) ON CONFLICT("message_id") DO UPDATE SET "star_count"=? RETURNING "star_count", "starboard_id"', (payload.message_id, payload.guild_id, payload.channel_id, count, count))
            star_count, starboard_id = await cursor.fetchone()
            cursor = await self.bot.db.execute('SELECT "star_min","channel" FROM "starboard_config" WHERE "guild_id"=?', (payload.guild_id,))
            min_stars, channel = await cursor.fetchone()

            if min_stars is not None and star_count >= min_stars:
                channel = self.bot.get_channel(channel)
                embed = nextcord.Embed(title=str(star_count)+" ⭐ message in #"+reaction_channel.name,
                        url=message.jump_url,
                        description=message.content,
                        timestamp=message.created_at)

                embed.set_author(name=message.author.display_name,
                        icon_url=message.author.avatar.url)

                if message.attachments and message.attachments[0].content_type.startswith("image"):
                    embed.set_image(url=message.attachments[0].url)

                if starboard_id is None:
                    starboard_msg = await channel.send(embed=embed)
                    starboard_id = starboard_msg.id
                    await self.bot.db.execute('UPDATE "starboard" SET "starboard_id"=? WHERE "message_id"=?', (starboard_id,message.id))
                else:
                    message = await channel.fetch_message(starboard_id)
                    await message.edit(embed=embed)

            await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload:nextcord.RawReactionActionEvent): 
        """
        Update starboard score when a reaction is removed.
        """
        cursor = await self.bot.db.execute('SELECT * FROM "starboard_config" WHERE "guild_id"=?', (payload.guild_id,))
        if await cursor.fetchone() is None: 
            return

        if payload.emoji.name == '⭐':
            reaction_channel = self.bot.get_channel(payload.channel_id)
            message = await reaction_channel.fetch_message(payload.message_id)
            try:
                count = list(filter(lambda r: r.emoji == '⭐', message.reactions))[0].count
            except IndexError:
                count = 0
            cursor = await self.bot.db.execute('INSERT INTO "starboard" ("message_id", "guild_id", "channel_id", "star_count") VALUES (?,?,?,?) ON CONFLICT("message_id") DO UPDATE SET "star_count"=? RETURNING "star_count", "starboard_id"', (payload.message_id, payload.guild_id, payload.channel_id, count, count))
            star_count, starboard_id = await cursor.fetchone()
            cursor = await self.bot.db.execute('SELECT "star_min","channel" FROM "starboard_config" WHERE "guild_id"=?', (payload.guild_id,))
            min_stars, channel = await cursor.fetchone()

            await self.bot.db.commit()

            if starboard_id is not None:
                channel = self.bot.get_channel(channel)
                embed = nextcord.Embed(title=str(star_count)+" ⭐ message in #"+reaction_channel.name,
                        url=message.jump_url,
                        description=message.content,
                        timestamp=message.created_at)

                embed.set_author(name=message.author.display_name,
                        icon_url=message.author.avatar.url)

                if message.attachments and message.attachments[0].content_type.startswith("image"):
                    embed.set_image(url=message.attachments[0].url)

                message = await channel.fetch_message(starboard_id)
                await message.edit(embed=embed)

    @commands.command(usage='[minimum stars|subcommand]', aliases=[])
    async def starboard(self, ctx:commands.Context, min_stars:int=3):
        """
        Initialize starboard for a server
        Run this command in the channel to be used for starboard with the minimum number of stars to be pinned. Default is 3.
        """
        await self.bot.db.execute('REPLACE INTO "starboard_config" ("guild_id", "star_min", "channel") VALUES (?,?,?)', (ctx.guild.id, min_stars, ctx.channel.id))
        await self.bot.db.commit()
        await ctx.send("Starboard initialized! React to messages with ⭐ to add them to starboard!")


    @commands.command(usage='', aliases=[])
    async def random(self, ctx:commands.Context):
        """
        Get a random starboard message from this server
        """
        cursor = await self.bot.db.execute('SELECT "message_id","channel_id","star_count" FROM "starboard" WHERE "guild_id"=? AND "star_count">=(SELECT "star_min" FROM "starboard_config" WHERE "guild_id"=?)', (ctx.guild.id, ctx.guild.id))
        messages = await cursor.fetchall()
        if not messages:
            await ctx.send("There are no starboard messages in this server!")

        msg = random.choice(messages)
        channel = self.bot.get_channel(msg[1])
        message = await channel.fetch_message(msg[0])
        star_count = msg[2]
        
        embed = nextcord.Embed(title=str(star_count)+" ⭐ message in #"+channel.name,
                url=message.jump_url,
                description=message.content,
                timestamp=message.created_at)

        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.avatar.url)

        if message.attachments and message.attachments[0].content_type.startswith("image"):
            embed.set_image(url=message.attachments[0].url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Starboard(bot))
