import aiohttp

import aoi
from discord.ext import commands, tasks


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


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Utility(bot))
