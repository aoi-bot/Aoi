from typing import List

import discord
from discord.ext import commands

import aoi


class Messages(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to deal with messages"

    @commands.has_permissions(manage_messages=True)
    @commands.command(
        brief="Lists the users who have not reacted to a message"
    )
    async def noreactions(self, ctx: aoi.AoiContext, msg: discord.Message):
        m: discord.Member
        r: discord.Reaction
        lst: List[int] = []
        for r in msg.reactions:
            for u in await r.users().flatten():
                if u.id not in lst and not u.bot:
                    lst.append(u.id)
        if not lst:
            return await ctx.send_info("No one reacted")
        await ctx.paginate(
            lst=[f"<@{u.id}> | {u}" for u in ctx.guild.members if u.id not in lst],
            n=30,
            title="Members who did not react"
        )

    @commands.has_permissions(manage_messages=True)
    @commands.command(
        brief="Lists the users who have reacted to a message"
    )
    async def reactions(self, ctx: aoi.AoiContext, msg: discord.Message):
        m: discord.Member
        r: discord.Reaction
        lst: List[int] = []
        for r in msg.reactions:
            for u in await r.users().flatten():
                if u.id not in lst and not u.bot:
                    lst.append(u.id)
        if not lst:
            return await ctx.send_info("No one reacted.")
        await ctx.paginate(
            lst=[f"<@{u}> | {ctx.guild.get_member(u)}" for u in lst],
            n=30,
            title="Members who reacted"
        )

    @commands.has_permissions(manage_messages=True)
    @commands.command(
        brief="Send a message with Aoi. Use [this site](https://embed.aoibot.xyz/) to make the embed."
    )
    async def say(self, ctx: aoi.AoiContext, *, msg: str):
        await ctx.send_json(msg)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Messages(bot))
