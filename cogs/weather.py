import logging
from typing import Optional

import discord
from discord.ext import commands
import aoi
from wrappers import weather as wx
from libs.converters import latlong
from wrappers import gmaps as gmaps

class Weather(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.wx: Optional[wx.WeatherGov] = None
        bot.loop.create_task(self._init())

    async def _init(self):
        logging.info("wx:Waiting for bot")
        await self.bot.wait_until_ready()
        self.wx = wx.WeatherGov(self.bot.weather_gov)
        logging.info("Ready!")

    @property
    def description(self):
        return "Look up weather data for a location"


    @commands.command(
        brief="Look up a current satellite image"
    )
    async def satellite(self, ctx: aoi.AoiContext,
                        lat: latlong(), long: latlong()):
        raise NotImplemented

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
