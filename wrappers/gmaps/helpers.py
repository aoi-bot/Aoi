from __future__ import annotations


from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from discord.ext import commands

if TYPE_CHECKING:
    import aoi

def try_convert_coord(arg: str):
    arg = arg.lower().replace("°", "")
    try:
        if arg.endswith("e") or arg.endswith("n"):
            n = float(arg[:-1])
        elif arg.endswith("s") or arg.endswith("w"):
            n = -float(arg[:-1])
        else:
            n = float(arg)
    except ValueError:
        raise commands.BadArgument("Value must be in the format -9.9N, -9.9")
    if not (-180 <= n <= 180):
        raise commands.BadArgument("Value out of range")
    return n


@dataclass(frozen=True)
class LocationComponent:
    short: str
    long: str
    type: List[str]


class LocationCoordinates:

    def __init__(self, lat: float, long: float, location: str=None):
        self.lat = lat
        self.long = long
        self.location = location

    def __str__(self):
        return f"{abs(self.lat):.8}°{'N' if self.lat > 0 else 'S'} " \
               f"{abs(self.long):.8}°{'E' if self.long > 0 else 'W'} "

    @classmethod
    async def convert(cls, ctx: aoi.AoiContext, arg: str):
        # try lat/long lookup first
        spl = arg.split()
        if len(spl) == 2:
            try:
                return cls(
                    lat=try_convert_coord(spl[0]),
                    long=try_convert_coord(spl[1])
                )
            except commands.BadArgument:
                pass
        # now try google maps
        res = await ctx.bot.gmap.lookup_address(arg)
        if not res:
            raise commands.BadArgument("Invalid location")
        return cls(
            res[0].geometry.location.lat,
            res[0].geometry.location.long,
            res[0].formatted_address
        )


@dataclass(frozen=True)
class LocationGeometry:
    northeast: Optional[LocationCoordinates]
    southwest: Optional[LocationCoordinates]
    location: LocationCoordinates
    location_type: str


@dataclass(frozen=True)
class Location:
    address_components: List[LocationComponent]
    formatted_address: str
    geometry: LocationGeometry
