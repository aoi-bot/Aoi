from __future__ import annotations

import colorsys
import datetime
import math
import re
import typing

import dateparser
import discord
import webcolors
from discord.ext import commands
from discord.ext.commands import BadArgument

duration_parser = re.compile(
    r"((?P<days>\d+?) ?(days|day|D|d) ?)?"
    r"((?P<hours>\d+?) ?(hours|hour|H|h) ?)?"
    r"((?P<minutes>\d+?) ?(minutes|minute|M|m) ?)?"
    r"((?P<seconds>\d+?) ?(seconds|second|S|s))?"
)


def t_delta() -> typing.Callable[[str], datetime.timedelta]:
    """Convert duration strings into timedelta objects."""

    def convert(arg: str) -> datetime.timedelta:
        """
        Converts a `duration` string to a timedelta object.
        The converter supports the following symbols for each unit of time:
        - days: `d`, `D`, `day`, `days`
        - hours: `H`, `h`, `hour`, `hours`
        - minutes: `M`, `minute`, `minutes`
        - seconds: `S`, `s`, `second`, `seconds`
        The units need to be provided in descending order of magnitude.
        """
        try:
            seconds = int(arg)
            delta = datetime.timedelta(seconds=seconds)
        except ValueError:
            match = duration_parser.fullmatch(arg)
            if not match:
                raise BadArgument(f"`{arg}` is not a valid duration string.")

            duration_dict = {
                unit: int(amount) for unit, amount in match.groupdict(default=0).items()
            }
            delta = datetime.timedelta(**duration_dict)

        return delta

    return convert


class AoiColor:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    @classmethod
    async def convert(cls, arg: str) -> "AoiColor":  # noqa C901
        orig = arg
        arg = arg.lower().strip("#x")
        if arg == "maddiepurple":
            arg = "a781e7"
        if arg.startswith("0x"):
            arg = arg
        try:
            clr = webcolors.html5_parse_simple_color(webcolors.name_to_hex(arg))
            return cls(clr.red, clr.green, clr.blue)
        except ValueError:
            pass
        if len(arg) == 6:
            try:
                clr = webcolors.html5_parse_simple_color(f"#{arg}")
                return cls(clr.red, clr.green, clr.blue)
            except ValueError:
                raise commands.BadColourArgument(orig)
        elif len(arg) == 3:
            try:
                clr = webcolors.html5_parse_simple_color(
                    "#" + "".join(f"{c}{c}" for c in arg)
                )
                return cls(clr.red, clr.green, clr.blue)
            except ValueError:
                raise ValueError(orig)
        raise ValueError(orig)

    def __str__(self):
        return f"{self.r:02x}{self.g:02x}{self.b:02x}"

    def to_rgb(self):
        return self.r, self.g, self.b

    def to_discord_color(self):
        return discord.Colour.from_rgb(self.r, self.g, self.b)

    def to_hls(self):
        return colorsys.rgb_to_hls(*(x / 256 for x in self.to_rgb()))


class FuzzyAoiColor(AoiColor):
    def __init__(self, r: int, g: int, b: int, *, attempt: str = None):
        super(FuzzyAoiColor, self).__init__(r, g, b)
        self.attempt = attempt

    @classmethod
    async def convert(cls, arg: str) -> "AoiColor":
        orig = arg
        arg = arg.lower().strip("#x")
        if arg.startswith("0x"):
            arg = arg
        try:
            clr = webcolors.html5_parse_simple_color(webcolors.name_to_hex(arg))
            return cls(clr.red, clr.green, clr.blue)
        except ValueError:
            pass
        if len(arg) == 6:
            try:
                clr = webcolors.html5_parse_simple_color(f"#{arg}")
                return cls(clr.red, clr.green, clr.blue)
            except ValueError:
                return cls(0, 0, 0, attempt=orig)
        elif len(arg) == 3:
            try:
                clr = webcolors.html5_parse_simple_color(
                    "#" + "".join(f"{c}{c}" for c in arg)
                )
                return cls(clr.red, clr.green, clr.blue)
            except ValueError:
                return cls(0, 0, 0, attempt=orig)
        return cls(0, 0, 0, attempt=orig)


async def partial_emoji_convert(ctx: AoiContext, arg: str) -> discord.PartialEmoji:
    match = re.match(r"<(a?):([a-zA-Z0-9_]+):([0-9]+)>$", arg)

    if match:
        emoji_animated = bool(match.group(1))
        emoji_name = match.group(2)
        emoji_id = int(match.group(3))

        return discord.PartialEmoji.with_state(
            ctx.bot._connection, animated=emoji_animated, name=emoji_name, id=emoji_id
        )

    return discord.PartialEmoji.with_state(ctx.bot._connection, name=arg)
