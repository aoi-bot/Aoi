import math

from discord.ext import commands

import aoi
from libs.converters import integer, allowed_strings
from libs.expressions import evaluate


def _get_prime_factors(number):
    pfact = {}
    if number < 0:
        pfact[-1] = 1
    number = abs(number)
    if number == 1:
        pfact[1] = 1
        return pfact
    while number % 2 == 0:
        number = number // 2
        pfact[2] = pfact.get(2, 0) + 1
    for i in range(3, int(math.sqrt(number)) + 1, 2):
        while number % i == 0:
            number = number // i
            pfact[i] = pfact.get(i, 0) + 1
    if number > 2:
        pfact[number] = pfact.get(number, 0) + 1
    return pfact


def _inlimits(number):
    if number > 100000000000:
        raise commands.BadArgument("Number must be less than 100000000000")


class Math(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to do basic math"

    @commands.command(
        brief="Find the prime factorization of a number",
        aliases=["pfact", "factor"]
    )
    async def primefactor(self, ctx: aoi.AoiContext, number: integer(max_digits=8)):
        pfact = _get_prime_factors(number)
        await ctx.send_info(
            f"Prime factorization of {number} is ```\n"
            f"{'*'.join((str(n) + '^' + str(c) if c > 1 else str(n)) for n, c in pfact.items())}\n"
            f"```",
            user=None
        )

    @commands.command(
        brief="Checks to see if a number is prime"
    )
    async def isprime(self, ctx: aoi.AoiContext, number: integer(max_digits=8,
                                                                 force_positive=True)):
        await ctx.send_info(
            f"{number} is {'not' if len(_get_prime_factors(number).keys()) > 1 else ''} prime"
        )

    @commands.command(
        brief="Evaluates an expression"
    )
    async def calc(self, ctx: aoi.AoiContext, *, expr: str):
        res = await evaluate(expr)
        await ctx.send_info(f"Expression Result:\n{res}")

    @commands.command(
        brief="Converts between bases",
        aliases=["baseconv", "bconv"]
    )
    async def baseconvert(self, ctx: aoi.AoiContext,
                          base1: allowed_strings("hex", "dec", "bin", "oct"),
                          base2: allowed_strings("hex", "dec", "bin", "oct"),
                          value: str):
        try:
            dec = int(value, {"hex": 16,
                              "dec": 10,
                              "bin": 2,
                              "oct": 8}[base1])
        except ValueError:
            raise commands.BadArgument(f"\n{value} is not a valid {base1} number")
        conv = {"hex": hex,
                "dec": int,
                "bin": bin,
                "oct": oct}[base2](dec)
        if base2 == "dec":
            return await ctx.send_info(f"\n{base1} `{value}` is {base2} `{conv:,}`")
        return await ctx.send_info(f"\n{base1} `{value}` is {base2} `{conv}`")

    @commands.command(
        brief="Multiply two large numbers",
        aliases=["bmult"]
    )
    async def bigmultiply(self, ctx: aoi.AoiContext,
                          num1: int,
                          num2: int):
        await ctx.send_info(f"\n`{num1:,}` * `{num2:,}` = `{num1 * num2:,}`")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Math(bot))
