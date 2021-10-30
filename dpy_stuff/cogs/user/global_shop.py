import discord
from discord.ext import commands

import bot
from libs.currency_classes import CurrencyLock


class GlobalShop(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands for managing and using the global shop"

    @commands.command(brief="Pay someone global currency.")
    async def pay_g(self, ctx: bot.AoiContext, member: discord.Member, amount: int):
        async with CurrencyLock(ctx, amount, True, f"Paid ${amount} to {member}"):
            await self.bot.db.ensure_global_currency_entry(member)
            await self.bot.db.award_global_currency(member, amount)

    @commands.is_owner()
    @commands.command(brief="Add a title to the shop")
    async def add_title_g(self, ctx: bot.AoiContext, title: str, amount: int):
        await ctx.confirm_coro(
            f"Add `{title}` for ${amount:,}?",
            f"`{title}` added for ${amount:,}.",
            f"`{title}` not added.",
            self.bot.db.conn.execute(
                "insert into title_shop (title, cost) values (?,?)", (title, amount)
            ),
        )
        await self.bot.db.conn.commit()

    @commands.command(brief="Lists the available titles")
    async def titleshop(self, ctx: bot.AoiContext):
        await ctx.paginate(
            [
                f"**{r[0]} - ${r[2]:,}**\n{r[1]}\n"
                for r in await (
                    await self.bot.db.conn.execute("select * from title_shop")
                ).fetchall()
            ],
            title="Title Shop",
            n=10,
            fmt=f"%s\n\nDo `{ctx.prefix}buytitle n` to buy a title.",
        )

    @commands.command(brief="Buys a title")
    async def buytitle(self, ctx: bot.AoiContext, num: int):
        await self.bot.db.ensure_user_entry(ctx.author)
        r = await (
            await self.bot.db.conn.execute(
                "select * from title_shop where id=?", (num,)
            )
        ).fetchone()
        if not r:
            return await ctx.send_error(
                f"Title with ID `{num}` does not exist. Do `{ctx.prefix}titleshop` to list "
                f"the available titles"
            )

        amt = r[2]
        title = r[1]

        if amt > await self.bot.db.get_global_currency(ctx.author):
            return await ctx.send_error("That title costs more than you have")

        for r in self.bot.db.owned_titles[ctx.author.id]:
            if title.lower() == r.lower():
                return await ctx.send_error("You already own that title")

        _ = await ctx.confirm(
            f"Buy `{title}` for ${amt:,}?",
            f"Bought `{title}` for ${amt:,}. Do `{ctx.prefix}mytitles` to see your titles.",
            f"Cancelled purchase",
        )

        if amt > await self.bot.db.get_global_currency(ctx.author):
            return await ctx.send_error("That title costs more than you have")

        await self.bot.db.award_global_currency(ctx.author, -amt)
        await self.bot.db.add_title(ctx.author, title)

    @commands.command(brief="Lists your titles")
    async def mytitles(self, ctx: bot.AoiContext):
        await ctx.paginate(
            [
                f"**{n}** - {v}\n"
                for n, v in enumerate(self.bot.db.owned_titles[ctx.author.id])
            ],
            title="Owned titles",
            n=10,
            fmt=f"%s\n\nDo `{ctx.prefix}equiptitle n` to set your profile title.",
        )

    @commands.command(brief="Equip a title")
    async def equiptitle(self, ctx: bot.AoiContext, num: int):
        try:
            await self.bot.db.equip_title(ctx.author, num)
            await ctx.send_ok("Title equipped!")
        except IndexError:
            await ctx.send_error(
                f"You don't own a title with that index. Do `{ctx.prefix}mytitles` to "
                f"view your titles"
            )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(GlobalShop(bot))
