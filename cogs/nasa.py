import io

import aiohttp
import discord
from discord.ext import commands
import aoi
from libs.converters import latlong

class Nasa(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "A collection of commands to look up data from NASA"

    @commands.command(
        brief="Get a LANDSAT-8 image of a location"
    )
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def landsat(self, ctx: aoi.AoiContext, lat: latlong(), long: latlong()):
        url = f"https://api.nasa.gov/planetary/earth/imagery?" \
              f"lon={long}&lat={lat}&dim=0.15&api_key={self.bot.nasa}"
        buf = io.BytesIO()
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    buf.write(await resp.content.read())
        await ctx.embed(
            title=f"{lat} {long}",
            image=buf
        )



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Nasa(bot))
