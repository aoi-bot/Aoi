from typing import Union

import discord
from discord.ext import commands
import aoi
from libs.currency_classes import CurrencyLock


class ServerShop(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.command(
        brief="Pay someone server currency."
    )
    async def pay(self, ctx: aoi.AoiContext, member: discord.Member, amount: int):
        async with CurrencyLock(ctx, amount, False, f"Paid ${amount} to {member}"):
            await self.bot.db.ensure_guild_currency_entry(member)
            await self.bot.db.award_guild_currency(member, amount)

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Add a role to the shop",
        aliases=["shopradd","shopra"]
    )
    async def shoproleadd(self, ctx: aoi.AoiContext, role: discord.Role, cost: int):
        await self.bot.db.add_guild_shop_role(ctx.guild, role, cost)
        await ctx.send_ok(f"Added {role.mention} to the shop for ${cost}")

    @commands.command(
        brief="View server shop"
    )
    async def shop(self, ctx: aoi.AoiContext):
        shop = await self.bot.db.get_guild_shop(ctx.guild)
        if not shop:
            return await ctx.send_info(f"{ctx.guild} has no shop set up.")
        await ctx.paginate(
            [f"${s.cost} - <@&{s.data}> ({s.data})" for s in shop],
            7,
            title=f"{ctx.guild} Server Shop",
            fmt=f"%s\n\nDo `{ctx.prefix}buy role_number` to buy a role"
        )

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Remove a role from the server shop",
        aliases=["shoprrem", "shoprr"]
    )
    async def shoproleremove(self, ctx: aoi.AoiContext, role: Union[discord.Role, int]):
        await self.bot.db.del_guild_shop_item(ctx.guild, "role", str(role if isinstance(role, int) else role.id))
        await ctx.send_ok(f"Removed {role if isinstance(role, int) else role.mention}.")

    @commands.command(
        brief="Buy a role from the shop"
    )
    async def buyrole(self, ctx: aoi.AoiContext, role: Union[discord.Role, str]):
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






def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(ServerShop(bot))
