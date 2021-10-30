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

if typing.TYPE_CHECKING:
    from bot.custom_context import AoiContext


def allowed_strings(
    *values, preserve_case: bool = False
) -> typing.Callable[[str], str]:
    def converter(arg: str) -> str:
        if not preserve_case:
            arg = arg.lower()

        if arg not in values:
            raise commands.BadArgument(
                f"Only the following values are allowed:\n```{', '.join(values)}```"
            )
        else:
            return arg

    return converter


def disenable() -> typing.Callable[[str], str]:
    def converter(arg: str) -> str:
        true = ["enable", "on", "true"]
        false = ["disable", "off", "false"]

        if arg.lower() not in true + false:
            raise commands.BadArgument(
                f"Allowed values: " + ", ".join(f"`{v}`" for v in true + false)
            )
        else:
            return "enable" if arg.lower() in true else "disable"

    return converter


def integer(*, max_digits=10, force_positive=False) -> typing.Callable[[str], int]:
    def converter(arg: str) -> int:
        arg = arg.replace(",", "")

        try:
            n = int(arg)
        except ValueError:
            raise commands.BadArgument(f"`{arg}` is not a valid integer")
        if math.log(abs(n), 10) > max_digits:
            raise commands.BadArgument(f"`{arg}` must be less than {max_digits} digits")
        if abs(n) != n and force_positive:
            raise commands.BadArgument(f"`{arg}` must be a positive integer")
        try:
            _n = float(n)
        except ValueError:
            pass
        # noinspection PyUnboundLocalVariable
        if n != _n:
            raise commands.BadArgument(f"`{arg}` is not a valid integer")
        return n

    return converter


def latlong() -> typing.Callable[[str], float]:
    def converter(arg: str) -> float:
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

    return converter


def dtime() -> typing.Callable[[str], datetime.datetime]:
    def converter(arg: str) -> datetime.datetime:
        n = dateparser.parse(
            arg,
            [
                "%m/%d/%y",
                "%m-%d-%y",
                "%-m-%-d-%Y",
            ],
        )
        if not n:
            raise commands.BadArgument("Invalid date")
        return n

    return converter


def rolename() -> typing.Callable[[str], str]:
    def converter(arg: str) -> str:
        if len(arg) > 32:
            raise commands.BadArgument("Role name too long")
        return arg

    return converter


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
    async def convert(
        cls, ctx: typing.Union[AoiContext, SlashContext], arg: str
    ) -> "AoiColor":  # noqa C901
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
                raise commands.BadColourArgument(orig)
        raise commands.BadColourArgument(orig)

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
    async def convert(cls, ctx: AoiContext, arg: str) -> "AoiColor":
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
