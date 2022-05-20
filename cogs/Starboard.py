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

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.db.execute(
            'CREATE TABLE IF NOT EXISTS "starboard" ("message_id" INTEGER PRIMARY KEY, "guild_id" INTEGER NOT NULL, "channel_id" INTEGER NOT NULL, "star_count" INTEGER NOT NULL, "starboard_id" INTEGER)'
        )
        
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        """
        Update starboard score when a reaction is added.
        """
        cursor = await self.bot.db.execute('SELECT "starboard","star_min" FROM "guilds" WHERE "guild_id"=?', (payload.guild_id,))
        starboard_exists = await cursor.fetchone() 
        if starboard_exists is None or starboard_exists == (None,None):
            # Starboard is not set up on this guild
            return

        if payload.emoji.name == '⭐':
            reaction_channel = self.bot.get_channel(payload.channel_id)
            message = await reaction_channel.fetch_message(payload.message_id)
            try:
                count = list(
                    filter(
                        lambda r: r.emoji == '⭐',
                        message.reactions))[0].count
            except IndexError:
                count = 0

            await self.bot.db.execute('INSERT INTO "starboard" ("message_id", "guild_id", "channel_id", "star_count") VALUES (?,?,?,?) ON CONFLICT("message_id") DO UPDATE SET "star_count"=?', (payload.message_id, payload.guild_id, payload.channel_id, count, count))
            cursor = await self.bot.db.execute('SELECT "star_count","starboard_id" FROM "starboard" WHERE "message_id"=?', (payload.message_id,))
            star_count, starboard_id = await cursor.fetchone()
            cursor = await self.bot.db.execute('SELECT "star_min","starboard" FROM "guilds" WHERE "guild_id"=?', (payload.guild_id,))
            min_stars, channel = await cursor.fetchone()

            if min_stars is not None and star_count >= min_stars:
                channel = self.bot.get_channel(channel)
                embed = nextcord.Embed(
                    title=str(star_count) +
                    " ⭐ message in #" +
                    reaction_channel.name,
                    url=message.jump_url,
                    description=message.content,
                    timestamp=message.created_at)

                embed.set_author(name=message.author.display_name,
                                 icon_url=message.author.avatar.url)

                if message.attachments and message.attachments[0].content_type.startswith(
                        "image"):
                    embed.set_image(url=message.attachments[0].url)

                if starboard_id is None:
                    starboard_msg = await channel.send(embed=embed)
                    starboard_id = starboard_msg.id
                    await self.bot.db.execute('UPDATE "starboard" SET "starboard_id"=? WHERE "message_id"=?', (starboard_id, message.id))
                else:
                    message = await channel.fetch_message(starboard_id)
                    await message.edit(embed=embed)

            await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: nextcord.RawReactionActionEvent):
        """
        Update starboard score when a reaction is removed.
        """
        cursor = await self.bot.db.execute('SELECT "starboard","star_min" FROM "guilds" WHERE "guild_id"=?', (payload.guild_id,))
        starboard_exists = await cursor.fetchone() 
        if starboard_exists is None or starboard_exists == (None,None):
            # Starboard is not set up on this guild
            return

        if payload.emoji.name == '⭐':
            reaction_channel = self.bot.get_channel(payload.channel_id)
            message = await reaction_channel.fetch_message(payload.message_id)
            try:
                count = list(
                    filter(
                        lambda r: r.emoji == '⭐',
                        message.reactions))[0].count
            except IndexError:
                count = 0
            await self.bot.db.execute('INSERT INTO "starboard" ("message_id", "guild_id", "channel_id", "star_count") VALUES (?,?,?,?) ON CONFLICT("message_id") DO UPDATE SET "star_count"=?', (payload.message_id, payload.guild_id, payload.channel_id, count, count))
            cursor = await self.bot.db.execute('SELECT "star_count","starboard_id" FROM "starboard" WHERE "message_id"=?', (payload.message_id,))
            star_count, starboard_id = await cursor.fetchone()
            cursor = await self.bot.db.execute('SELECT "star_min","starboard" FROM "guilds" WHERE "guild_id"=?', (payload.guild_id,))
            min_stars, channel = await cursor.fetchone()

            await self.bot.db.commit()

            if starboard_id is not None:
                channel = self.bot.get_channel(channel)
                embed = nextcord.Embed(
                    title=str(star_count) +
                    " ⭐ message in #" +
                    reaction_channel.name,
                    url=message.jump_url,
                    description=message.content,
                    timestamp=message.created_at)

                embed.set_author(name=message.author.display_name,
                                 icon_url=message.author.avatar.url)

                if message.attachments and message.attachments[0].content_type.startswith(
                        "image"):
                    embed.set_image(url=message.attachments[0].url)

                message = await channel.fetch_message(starboard_id)
                await message.edit(embed=embed)

    @nextcord.slash_command()
    async def starboard(self, interaction:nextcord.Interaction):
        """
        Starboard base command.
        """
        pass

    @starboard.subcommand()
    async def info(self, interaction:nextcord.Interaction):
        """
        See starboard info on this server and use starboard subcommands
        """
        if isinstance(interaction.channel, nextcord.PartialMessageable):
            await interaction.send("This command can only be used in guilds.", ephemeral=True)
            return
        cursor = await self.bot.db.execute('SELECT "starboard","star_min" FROM "guilds" WHERE "guild_id"=?', (ctx.guild.id,))
        starboard_exists = await cursor.fetchone() 
        if starboard_exists is None or starboard_exists == (None,None):
            await interaction.send("Starboard has not been set up on this server!", ephemeral=True)
            return

        channel, star_min = starboard_exists

        embed = nextcord.Embed(title="Starboard info on " + ctx.guild.name)
        embed.add_field(name="Minimum Stars", value=str(star_min))
        embed.add_field(
            name="Starboard Channel", value=str(
                self.bot.get_channel(channel).mention))

        await interaction.send(embed=embed, ephemeral=True)

    @starboard.subcommand()
    async def setup(self, interaction:nextcord.Interaction, min_stars:int=3):
        """
        Initialize starboard for a server
        Run this command in the channel to be used for starboard with the minimum number of stars to be pinned. Default is 3.
        """
        if isinstance(interaction.channel, nextcord.PartialMessageable):
            await interaction.send("This command can only be used in guilds.", ephemeral=True)
            return
        if not interaction.permissions.manage_guild:
            await interaction.send("Only users with the `Manage Guild` permission can use this command.", ephemeral=True)
        await self.bot.db.execute('INSERT INTO "guilds" ("guild_id", "star_min", "starboard") VALUES (?,?,?) ON CONFLICT("guild_id") DO UPDATE SET "star_min"=?, "starboard"=?', (ctx.guild.id, min_stars, ctx.channel.id, min_stars, ctx.channel.id))
        await self.bot.db.commit()
        await interaction.send("Starboard initialized! React to messages with ⭐ to add them to starboard!", ephemeral=True)

    @starboard.subcommand()
    async def random(self, interaction:nextcord.Interaction):
        """
        Get a random starboard message from this server
        """
        if isinstance(interaction.channel, nextcord.PartialMessageable):
            await interaction.send("This command can only be used in guilds.", ephemeral=True)
            return
        cursor = await self.bot.db.execute('SELECT "message_id","channel_id","star_count" FROM "starboard" WHERE "guild_id"=? AND "star_count">=(SELECT "star_min" FROM "guilds" WHERE "guild_id"=?)', (ctx.guild.id, ctx.guild.id))
        messages = await cursor.fetchall()
        if not messages:
            await interaction.send("There are no starboard messages in this server!", ephemeral=True)
            return

        msg = random.choice(messages)
        channel = self.bot.get_channel(msg[1])
        message = await channel.fetch_message(msg[0])
        star_count = msg[2]

        embed = nextcord.Embed(
            title=str(star_count) +
            " ⭐ message in #" +
            channel.name,
            url=message.jump_url,
            description=message.content,
            timestamp=message.created_at)

        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.avatar.url)

        if message.attachments and message.attachments[0].content_type.startswith(
                "image"):
            embed.set_image(url=message.attachments[0].url)
        await interaction.send(embed=embed)


def setup(bot):
    bot.add_cog(Starboard(bot))
