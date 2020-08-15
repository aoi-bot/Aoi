import datetime
import io
from typing import Dict, Tuple

import aiohttp
from discord.ext import commands

import aoi
from libs.converters import latlong, dtime
from wrappers import gmaps


class Nasa(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.apod_cache: Dict[str, Tuple[str, str, str, str]] = {}

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

    #@commands.cooldown(1, 360, type=commands.BucketType.user)
    @commands.command(
        brief="Gets the astronomy picture of the day"
    )
    async def apod(self, ctx: aoi.AoiContext, date: dtime() = None):
        if not date:
            date = datetime.datetime.now()
        dt = date.strftime('%Y-%m-%d')
        if dt not in self.apod_cache:
            async with ctx.typing():
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(f"https://api.nasa.gov/planetary/apod?api_key={self.bot.nasa}&"
                                        f"date={dt}") as resp:
                        js = await resp.json()
            hdurl = js["hdurl"]
            url = js["url"]
            expl = js["explanation"][:1900]
            title = js["title"]
            self.apod_cache[dt] = (title, hdurl, url, expl)
        else:
            title, hdurl, url, expl = self.apod_cache[dt]
        await ctx.embed(
            title=title,
            description=f"{expl}\n\n[Normal Resolution]({url})  [High Resolution]({hdurl})",
            image=url
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Nasa(bot))
