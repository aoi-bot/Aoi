import typing
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

