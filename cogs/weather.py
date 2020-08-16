from datetime import datetime
import io
import logging
from functools import reduce
from typing import Optional, Dict, Any, Tuple

import aiohttp
from PIL import Image
from discord.ext import commands

import aoi
from wrappers import gmaps as gmaps
from wrappers import weather as wx


class Weather(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.wx: Optional[wx.WeatherGov] = None
        bot.loop.create_task(self._init())
        self.sat_cache: Dict[str, Tuple[datetime, Any]] = {}

    async def _init(self):
        logging.info("wx:Waiting for bot")
        await self.bot.wait_until_ready()
        self.wx = wx.WeatherGov(self.bot.weather_gov)
        logging.info("Ready!")

    @property
    def description(self):
        return "Look up weather data for a location"

    @commands.command(
        brief="A map of the amount of rain from the current storm"
    )
    async def stormrain(self, ctx: aoi.AoiContext, location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat, location.long)
        radar = res.radar_station[-3:]
        await ctx.embed(
            image=f"https://radar.weather.gov/ridge/lite/NTP/{radar}_0.png"
        )

    @commands.command(
        brief="A map of the amount of rain from the last hour"
    )
    async def hourrain(self, ctx: aoi.AoiContext, location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat, location.long)
        radar = res.radar_station[-3:]
        await ctx.embed(
            image=f"https://radar.weather.gov/ridge/lite/N1P/{radar}_0.png"
        )

    @commands.command(
        brief="Look up a looping radar"
    )
    async def radarloop(self, ctx: aoi.AoiContext, location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat, location.long)
        radar = res.radar_station[-3:]
        await ctx.embed(
            image=f"https://radar.weather.gov/ridge/lite/N0R/{radar}_loop.gif"
        )

    @commands.command(
        brief="Look up a current satellite image",
        aliases=["radar"]
    )
    async def satellite(self, ctx: aoi.AoiContext,
                        location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat,
                                        location.long)
        radar = res.radar_station[-3:]
        if radar in self.sat_cache:
            diff = (datetime.now() - self.sat_cache[radar][0]).seconds
            if diff < 30*60:
                img = self.sat_cache[radar][1]
                buf = io.BytesIO()
                img.save(buf, format="png")
                return await ctx.embed(image=buf, footer=f"Cached from {diff//60}m{diff%60:2} ago")
            del self.sat_cache[radar]
        urls = [
            f"https://radar.weather.gov/ridge/Overlays/Topo/Short/{radar}_Topo_Short.jpg",
            f"https://radar.weather.gov/ridge/RadarImg/N0R/{radar}_N0R_0.gif",
            f"https://radar.weather.gov/ridge/Overlays/County/Short/{radar}_County_Short.gif",
            f"https://radar.weather.gov/ridge/Overlays/Rivers/Short/{radar}_Rivers_Short.gif",
            f"https://radar.weather.gov/ridge/Overlays/Highways/Short/{radar}_Highways_Short.gif",
            f"https://radar.weather.gov/ridge/Overlays/Cities/Short/{radar}_City_Short.gif",
            f"https://radar.weather.gov/ridge/Warnings/Short/{radar}_Warnings_0.gif",
            f"https://radar.weather.gov/ridge/Legend/N0R/{radar}_N0R_Legend_0.gif"
        ]
        imgs = []
        async with ctx.typing():
            async with aiohttp.ClientSession() as sess:
                for url in urls:
                    async with sess.get(url) as resp:
                        buf = io.BytesIO()
                        buf.write(await resp.content.read())
                        buf.seek(0)
                        imgs.append(Image.open(buf).convert("RGBA"))
        composite = reduce(lambda i1, i2: Image.alpha_composite(i1, i2), imgs)
        self.sat_cache[radar] = (datetime.now(), composite)
        buf = io.BytesIO()
        composite.save(fp=buf, format="png")
        await ctx.embed(
            image=buf
        )

    @commands.command(
        brief="View the raw data for a lat/long"
    )
    async def wxraw(self, ctx: aoi.AoiContext, *,
                    location: gmaps.LocationCoordinates):
        res = await self.wx.lookup_grid(location.lat,
                                        location.long)
        await ctx.embed(
            title=f"{res.point}",
            fields=[
                ("Grid", f"{res.grid_x},{res.grid_y}"),
                ("Radar", res.radar_station),
                ("Timezone", res.time_zone),
                ("Endpoints", f"[Hourly]({res.forecast_hourly_endpoint})\n"
                              f"[Grid]({res.forecast_grid_data_endpoint})\n"
                              f"[Extended]({res.forecast_endpoint})\n")
            ]
        )

    @commands.cooldown(1, 60, type=commands.BucketType.user)
    @commands.command(
        brief="Look up an hourly forecast"
    )
    async def wxhourly(self, ctx: aoi.AoiContext, *, location: gmaps.LocationCoordinates):
        conditions = (await self.wx.lookup_hourly(location))
        await ctx.paginate(
            fmt=f"Resolved Address: {location.location or location}```%s```\n",
            lst=[cond.line() for cond in conditions],
            n=24,
            title="Weather lookup",
            thumbnails=[c.icon for c in conditions[3::24]]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Weather(bot))
