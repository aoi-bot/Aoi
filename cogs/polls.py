import asyncio
from typing import Dict

import discord
from discord.ext import commands
import aoi


class Polls(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        bot.loop.create_task(self._init())

    async def _init(self):
        self.bot.logger.info("polls:Waiting for bot")
        await self.bot.wait_until_ready()
        self.bot.logger.info("polls:Ready!")

    @commands.command(
        brief="Starts a poll"
    )
    async def poll(self, ctx: aoi.AoiContext, *, content: str):
        poll = content.split(";;")
        if len(poll) == 1:
            msg = await ctx.send(embed=discord.Embed(
                title=poll[0]
            ))
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
        else:
            choices = ["1️⃣", "2️⃣", "3️⃣",
                       "4️⃣", "5️⃣", "6️⃣",
                       "7️⃣", "8️⃣", "9️⃣"]
            msg = await ctx.send(embed=discord.Embed(
                title=poll[0],
                description="\n".join(f"{choices[n]} {poll[n+1]}" for n in range(len(poll) - 1))
            ))
            for i in range(len(poll) - 1):
                await msg.add_reaction(choices[i])
                await asyncio.sleep(0.5)
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @property
    def description(self) -> str:
        return "Polls"


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Polls(bot))
