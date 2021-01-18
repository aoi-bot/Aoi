from io import BytesIO

import aiohttp
import sympy
from PIL import Image, ImageOps

import aoi
from discord.ext import commands, tasks
from libs.converters import integer, allowed_strings
from libs.expressions import evaluate, _get_prime_factors


class Utility(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.cur_rates = {}
        self._currency_update.start()

    @property
    def description(self) -> str:
        return "Various utility commands"

    @tasks.loop(hours=1)
    async def _currency_update(self):
        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://api.exchangeratesapi.io/latest?base=USD") as resp:
                self.cur_rates = {k: v for k, v in sorted((await resp.json())["rates"].items(), key=lambda x: x[0])}

    def _convert(self, amount: float, from_unit: str, to_unit: str):
        return amount / self.cur_rates[from_unit] * self.cur_rates[to_unit]

    @commands.command(brief="Convert currency")
    async def currency(self, ctx: aoi.AoiContext, amount: float, from_unit: str, to_unit: str):
        from_unit = from_unit.upper()
        to_unit = to_unit.upper()
        if from_unit not in self.cur_rates:
            return await ctx.send_error(f"Unknown currency unit {from_unit}. Allowed units: " +
                                        " ".join(self.cur_rates.keys()))
        if to_unit not in self.cur_rates:
            return await ctx.send_error(f"Unknown currency unit {to_unit}. Allowed units: " +
                                        " ".join(self.cur_rates.keys()))

        converted = self._convert(amount, from_unit, to_unit)

        await ctx.send_ok(f"**{amount:.2f}** {from_unit} = **{converted:.2f}** {to_unit}")

    @commands.command(brief="Shows the current exchange rates, with an optional base", aliases=["exchange"])
    async def exchangerates(self, ctx: aoi.AoiContext, base: str = "usd"):
        def _(val):
            int_part = int(val)
            float_part = f"{val - int_part:.6f}"[2:]
            return f"{int_part:>5}.{float_part}"

        base = base.upper()
        if base not in self.cur_rates:
            return await ctx.send_error(f"Unknown currency unit {base}. Allowed units: " +
                                        " ".join(self.cur_rates.keys()))
        await ctx.embed(title=f"Currency exchange rates from {base}",
                        description="```c\n" +
                                    "\n".join(f"1 {base} = {_(self._convert(1, base, unit))} {unit} | "  # noqa
                                              f"1 {unit} = {_(self._convert(1, unit, base))} {base}"  # noqa
                                              for unit in self.cur_rates.keys() if unit != base) +
                                    "```"
                        )

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
        try:
            res = await evaluate(expr)
        except aoi.CalculationSyntaxError:
            await ctx.send_error("Syntax error")
        except aoi.DomainError as e:
            await ctx.send_error(f"Domain error for {e}")
        except aoi.MathError:
            await ctx.send_error("Math error")
        else:
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

    @commands.command(
        brief="Render LaTeX",
    )
    async def latex(self, ctx: aoi.AoiContext, *, formula: str):
        await ctx.trigger_typing()
        buffer = BytesIO()
        try:
            sympy.preview(f"\\[{formula.strip('`')}\\]", viewer="BytesIO", outputbuffer=buffer)
        except RuntimeError:
            return await ctx.send_error("An error occurred while rendering.")
        result = BytesIO()
        buffer.seek(0)
        old = Image.open(buffer)
        ImageOps.expand(old, border=20, fill=(0xff, 0xff, 0xff)).save(result, format="png")
        await ctx.embed(image=result)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Utility(bot))
