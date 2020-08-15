from typing import Optional

import discord
from discord.ext import commands
import aoi
from wrappers import gmaps
import logging

class GeoLocation(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.gmap: Optional[gmaps.GeoLocation] = None
        bot.loop.create_task(self._init())

    async def _init(self):
        logging.info("geo:waiting for bot")
        await self.bot.wait_until_ready()
        self.gmap = gmaps.GeoLocation(self.bot.google)
        logging.info("geo:ready!")

    @property
    def description(self):
        return "Get geolocation data"

    @commands.command(
        brief="Get basic geolocation data on an address"
    )
    async def geolookup(self, ctx: aoi.AoiContext, *, address):
        result = (await self.gmap.lookup_address(address))[0]
        await ctx.embed(
            title="Geolocation Lookup",
            fields=[
                ("Looked up address", address),
                ("Resolved address", result.formatted_address),
                ("Location", result.geometry.location)
            ] + ([
                ("Bounds", f"{result.geometry.northeast}\n")
            ] if result.geometry.northeast else []),
            not_inline=[0, 1, 2]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(GeoLocation(bot))
