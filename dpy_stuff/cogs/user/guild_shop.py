from typing import Union

import discord
from discord.ext import commands

import bot
from libs.currency_classes import CurrencyLock


class ServerShop(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Guild role/item shop"

    @commands.command(brief="Pay someone server currency.")
    async def pay(self, ctx: bot.AoiContext, member: discord.Member, amount: int):
        async with CurrencyLock(ctx, amount, False, f"Paid ${amount} to {member}"):
            await self.bot.db.ensure_guild_currency_entry(member)
            await self.bot.db.award_guild_currency(member, amount)

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Add a role to the shop",
        aliases=["shopradd", "shopra", "shopaddrole", "shopar"],
    )
    async def shoproleadd(self, ctx: bot.AoiContext, role: discord.Role, cost: int):
        await self.bot.db.add_guild_shop_role(ctx.guild, role, cost)
        await ctx.send_ok(f"Added {role.mention} to the shop for ${cost}")

    @commands.command(brief="View server shop")
    async def shop(self, ctx: bot.AoiContext):
        shop = await self.bot.db.get_guild_shop(ctx.guild)
        if not shop:
            return await ctx.send_info(f"{ctx.guild} has no shop set up.")
        await ctx.paginate(
            [f"${s.cost} - <@&{s.data}> ({s.data})" for s in shop],
            7,
            title=f"{ctx.guild} Server Shop",
            fmt=f"%s\n\nDo `{ctx.prefix}buy role_number` to buy a role",
        )

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Remove a role from the server shop",
        aliases=["shoprrem", "shoprr", "shopremoverole", "shopremr"],
    )
    async def shoproleremove(self, ctx: bot.AoiContext, role: Union[discord.Role, int]):
        await self.bot.db.del_guild_shop_item(
            ctx.guild, "role", str(role if isinstance(role, int) else role.id)
        )
        await ctx.send_ok(f"Removed {role if isinstance(role, int) else role.mention}.")

    @commands.command(brief="Buy a role from the shop")
    async def buyrole(self, ctx: bot.AoiContext, role: Union[discord.Role, str]):
        shop = await self.bot.db.get_guild_shop(ctx.guild)
        if not shop:
            return await ctx.send_info(f"{ctx.guild} has no shop set up.")
        if isinstance(role, str):
            for i in ctx.guild.roles:
                if i.name.lower().replace(" ", "") == role.lower():
                    role = i
                    break
            else:
                raise commands.BadArgument("Role not found.")
        for i in shop:
            if i.type == "role" and i.data == str(role.id):
                found = i
                break
        else:
            return await ctx.send_error(f"{role.mention} is not in the shop.")
        if role.id in [r.id for r in ctx.author.roles]:
            return await ctx.send_info(f"You already have {role.mention}")
        async with CurrencyLock(ctx, found.cost, False, f"Bought {role.mention}"):
            await ctx.author.add_roles(role)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Award or take server currency.")
    async def award(self, ctx: bot.AoiContext, member: discord.Member, amount: int):
        await self.bot.db.award_guild_currency(member, amount)
        await ctx.send_ok(
            f"Awarded ${amount} to {member.mention}. Their new total is "
            f"{await self.bot.db.get_guild_currency(member)}"
        )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(ServerShop(bot))
