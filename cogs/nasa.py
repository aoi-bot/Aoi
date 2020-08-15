import datetime
import io

import aiohttp
import discord
from discord.ext import commands
import aoi
from wrappers import gmaps
from libs.converters import latlong, dtime


class Nasa(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "A collection of commands to look up data from NASA"

    @commands.command(
        brief="Get a LANDSAT-8 image of a lat/long"
    )
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def landsat(self, ctx: aoi.AoiContext, lat: latlong(), long: latlong(),
                      date: dtime() = None):
        dt = date or datetime.datetime.now()
        url = f"https://api.nasa.gov/planetary/earth/imagery?" \
              f"lon={long}&lat={lat}&dim=0.15&api_key={self.bot.nasa}" \
              f"&date={dt.strftime('%Y-%m-%d')}"
        buf = io.BytesIO()
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    buf.write(await resp.content.read())
        await ctx.embed(
            title=f"{lat} {long} {dt.strftime('%Y-%m-%d')}",
            image=buf
        )

    @commands.cooldown(1, 60, type=commands.BucketType.user)
    @commands.command(
        brief="Get a LANDSAT-8 image of a location"
    )
    async def landsatloc(self, ctx: aoi.AoiContext, place: str,
                         date: dtime() = None):
        gmap = gmaps.GeoLocation(self.bot.google)
        r = (await gmap.lookup_address(place))[0]
        lat = r.geometry.location.lat
        long = r.geometry.location.long
        dt = date or datetime.datetime.now()
        url = f"https://api.nasa.gov/planetary/earth/imagery?" \
              f"lon={long}&lat={lat}&dim=0.15&api_key={self.bot.nasa}" \
              f"&date={dt.strftime('%Y-%m-%d')}"
        buf = io.BytesIO()
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    buf.write(await resp.content.read())
        await ctx.embed(
            title=f"{lat} {long} {dt.strftime('%Y-%m-%d')}",
            description=r.formatted_address,
            image=buf
        )




def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Nasa(bot))
