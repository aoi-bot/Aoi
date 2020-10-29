import logging
from typing import Optional

from discord.ext import commands

import aoi
from wrappers import gmaps


class Geolocation(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.gmap: Optional[gmaps.GeoLocation] = None
        bot.loop.create_task(self._init())

    async def _init(self):
        self.bot.logger.info("geo:Waiting for bot")
        await self.bot.wait_until_ready()
        self.gmap = self.bot.gmap
        self.bot.logger.info("geo:ready!")

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
                            ("Bounds", f"{result.geometry.northeast}\n"
                                       f"{result.geometry.southwest}\n")
                        ] if result.geometry.northeast else []),
            not_inline=[0, 1, 2]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Geolocation(bot))
