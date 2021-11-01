from typing import List

import discord
import ksoftapi
from discord.ext import commands
from ksoftapi.models import LyricResult

from aoi import bot
from aoi.libs.misc import arg_or_0_index


class Searches(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Various search commands"

    @commands.command(brief="Search a tag on Imgur", aliases=["img"])
    async def imgur(self, ctx: bot.AoiContext, tag: str):
        try:
            (
                img_id,
                album_id,
                album_link,
                description,
            ) = await self.bot.imgur.random_by_tag(tag)
            await ctx.embed(
                title=description,
                description=f"[Link to post]({album_link})",
                title_url=album_link,
                image=f"https://i.imgur.com/{img_id}.jpg",
                footer=f'Imgur result for "{tag}" searched by {ctx.author}',
                trash_reaction=False,
            )
        except KeyError:
            await ctx.send_error("No results found with that tag")

    @commands.command(brief="Look up the lyrics for a song")
    async def lyrics(self, ctx: bot.AoiContext, *, query: str):
        # TODO re-enable this
        return await ctx.send_error("This command has been disabled temporarily while waiting on an API key")
        try:  # noqa
            lyrs: List[LyricResult] = sorted(await self.bot.ksoft.music.lyrics(query), key=lambda x: -x.search_score)
        except ksoftapi.NoResults:
            return await ctx.send_error("No results found.")

        if len(lyrs) > 1:
            await ctx.send_ok(
                f"\n" + "\n".join(f"{n + 1} - {res.name} - {res.artist}" for n, res in enumerate(lyrs[:10]))
            )
            n = await ctx.input(int, ch=lambda x: 1 <= x <= min(10, len(lyrs))) - 1
            if n is None:
                return
            lyr = lyrs[n]
        else:
            lyr = lyrs[0]

        lines = [line.strip() for line in lyr.lyrics.split("\n")]
        pages = [""]
        for line in lines:
            if len(pages[-1]) + len(line) > 1000:
                pages.append(line)
            else:
                pages[-1] += f"\n{line}"
        await ctx.page_predefined(
            *[
                discord.Embed(title=f"{lyr.name} -- {lyr.artist}", description=page)
                .set_footer(text="Powered by KSoft")  # noqa
                .set_thumbnail(url=lyr.album_art)
                for page in pages
            ]
            + [
                discord.Embed(
                    title=f"{lyr.name} -- {lyr.artist}",
                    description=f"Song: {lyr.name}\n"
                    f"Artist: {lyr.artist}\n"
                    f"Album: {lyr.album}\n"
                    f"Released in {arg_or_0_index(lyr.album_year)}\n",
                )
                .set_footer(text="Powered by KSoft")  # noqa
                .set_thumbnail(url=lyr.album_art)
            ]
        )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(Searches(bot))
