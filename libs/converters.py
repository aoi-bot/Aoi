import datetime
import math
import typing

import dateparser
from discord.ext import commands


def allowed_strings(*values, preserve_case: bool = False) \
        -> typing.Callable[[str], str]:
    """
    Return a converter which only allows arguments equal to one of the given values.
    Unless preserve_case is True, the argument is converted to lowercase. All values are then
    expected to have already been given in lowercase too.
    """

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


def disenable() \
        -> typing.Callable[[str], str]:
    """
    Return a converter which only allows arguments equal to one of the given values.
    Unless preserve_case is True, the argument is converted to lowercase. All values are then
    expected to have already been given in lowercase too.
    """

    def converter(arg: str) -> str:

        if arg.lower() not in ("enable", "disable"):
            raise commands.BadArgument(
                f"Only **enable** or **disable** are allowed."
            )
        else:
            return arg

    return converter


def integer(*, max_digits=10,
            force_positive=False) \
        -> typing.Callable[[str], int]:
    def converter(arg: str) -> int:
        arg = arg.replace(",", "")

        try:
            n = int(arg)
        except ValueError:
            raise commands.BadArgument(
                f"`{arg}` is not a valid integer"
            )
        if math.log(abs(n), 10) > max_digits:
            raise commands.BadArgument(
                f"`{arg}` must be less than {max_digits} digits"
            )
        if abs(n) != n and force_positive:
            raise commands.BadArgument(
                f"`{arg}` must be a positive integer"
            )
        try:
            _n = float(n)
        except ValueError:
            pass
        # noinspection PyUnboundLocalVariable
        if n != _n:
            raise commands.BadArgument(
                f"`{arg}` is not a valid integer"
            )
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
        n = dateparser.parse(arg,
                             [
                                 "%m/%d/%y",
                                 "%m-%d-%y",
                                 "%-m-%-d-%Y",
                             ])
        if not n:
            raise commands.BadArgument("Invalid date")
        return n

    return converter
