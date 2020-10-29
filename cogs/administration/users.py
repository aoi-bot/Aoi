import discord
from discord.ext import commands

import aoi


class Users(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return "Commands to manage users"

    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.command(brief="Set a member's nickname")
    async def setnick(self, ctx: aoi.AoiContext, member: discord.Member, *, nickname: str):
        if member.top_role >= ctx.me.top_role:
            raise aoi.RoleHierarchyError("I can't change the nickname of a person with a role higher than mine!")
        if member.top_role >= ctx.author.top_role:
            raise aoi.RoleHierarchyError("You can't change the nickname of a person with a role higher than yours!")
        await member.edit(nick=nickname)
        await ctx.send_ok(f"{member.mention}'s nickname set to {nickname}")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Users(bot))
