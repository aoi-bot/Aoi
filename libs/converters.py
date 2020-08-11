import typing
from discord.ext import commands

import math


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
        if n != _n:
            raise commands.BadArgument(
                f"`{arg}` is not a valid integer"
            )
        return n

    return converter

