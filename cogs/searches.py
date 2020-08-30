import io
import random
from typing import List

import aiohttp
from discord.ext import commands
from pixivapi import Illustration, Size

import aoi


class Searches(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Various search commands"

    @commands.command(
        brief="Search a tag on Imgur",
        aliases=["img"]
    )
    async def imgur(self, ctx: aoi.AoiContext, tag: str):
        try:
            img_id, album_id, album_link, description = await self.bot.imgur.random_by_tag(tag)
            await ctx.embed(
                title=description,
                description=f"[Link to post]({album_link})",
                title_url=album_link,
                image=f"https://i.imgur.com/{img_id}.jpg",
                footer=f"Imgur result for \"{tag}\" searched by {ctx.author}",
                trash_reaction=False
            )
        except KeyError:
            await ctx.send_error("No results found with that tag")

    @commands.command(
        brief="Search for a tag on Pixiv"
    )
    async def pixiv(self, ctx: aoi.AoiContext, tag: str):
        # i don't like that this library isn't async but eh
        #   maybe run it inside another thread eventually?
        async with ctx.typing():
            res: List[Illustration] = self.bot.pixiv.search_illustrations(tag)["illustrations"]
            filtered: List[Illustration] = []
            for n, r in enumerate(res):
                for t in r.tags:
                    if t["name"].lower() in self.bot.banned_pixiv_tags:
                        break
                else:
                    filtered.append(r)

        i = random.choice(filtered)

        buf = io.BytesIO()
        async with aiohttp.ClientSession() as sess:
            async with sess.get(i.image_urls[Size.ORIGINAL],
                                headers={
                                    "Referer": "https://www.pixiv.com/"
                                }) as resp:
                buf.write(await resp.read())

        buf.seek(0)

        await ctx.embed(
            image=buf,
            description=i.caption + f"\nhttps://www.pixiv.net/en/artworks/{i.id}",
            title=i.title,
            footer="  ".join([t["name"] for t in i.tags]),
            trash_reaction=False
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Searches(bot))
