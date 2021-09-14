import asyncio
import functools
import os

import capybre
import discord
from discord.ext import commands
from ebooklib import epub

from cogs.utils.ebook import downloader


class Ebook(commands.Cog):
    """
    Commands to download and work with ebooks.
    """
    def __init__(self, bot):
        self.bot = bot
        self.sites = {"https://archiveofourown.org/works/",
                      "https://www.wattpad.com/story/",
                      "https://www.fanfiction.net/s/",
                      "https://www.toonily.net/"}

    @commands.command(usage="<url>")
    async def download(self, ctx, url):
        """
        Download a fanfiction from wattpad.com, fanfiction.net, archiveofourown.org, or toonily.net.

        Make sure your link points to the table of contents for wattpad or toonily, or the first chapter for ffn or ao3.
        """
        if not any([url.startswith(s) for s in self.sites]):
            await ctx.message.reply("Make sure your link points to the table of contents for wattpad, or the first "
                                    "chapter for ffn or ao3")
        async with ctx.typing():
            fic = await asyncio.get_event_loop().run_in_executor(None, downloader.get_fic, url)
        if fic:
            async with ctx.typing():
                epub.write_epub('book.epub', fic, {})

                out = await asyncio.get_event_loop().run_in_executor(None,
                                                                     functools.partial(capybre.convert, 'book.epub',
                                                                                       output_file='out.epub',
                                                                                       as_ext='epub'))

            await ctx.message.reply(file=discord.File(out, 'fic.epub'))
            # print("Sent!")

            os.remove('book.epub')
            os.remove(out)
        else:
            await ctx.message.reply("Something went wrong. Make sure that your link points to the table of contents for"
                                    " wattpad or toonily, or the first chapter for ffn or ao3")

    @commands.command(usage="<desired format> (attachment: ebook to convert)")
    async def convert(self, ctx, ext):
        """
        Convert an ebook to another ebook format.
        """
        if not ctx.message.attachments:
            await ctx.message.reply("Please provide a file to convert")
        try:
            async with ctx.typing():
                attachment = ctx.message.attachments[0]
                await attachment.save(attachment.filename)
                out = await asyncio.get_event_loop().run_in_executor(None, functools.partial(capybre.convert,
                                                                                             attachment.filename,
                                                                                             output_file='out.' + ext,
                                                                                             as_ext=ext))
        except ValueError:
            await ctx.message.reply(
                "Something went wrong. Please check your inputs to ensure that the attached file is an ebook and the "
                "desired format is valid.")
        else:
            await ctx.message.reply(file=discord.File(out, 'fic.' + ext))

        try:
            os.remove(attachment.filename)
        except OSError:
            pass

        if out:
            os.remove(out)


def setup(bot):
    bot.add_cog(Ebook(bot))
