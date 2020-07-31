from functools import reduce

import discord
from discord.ext import commands
import aoi

class Aoi(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.is_owner()
    @commands.command()
    async def stats(self, ctx: aoi.AoiContext):
        text_channels = 0
        voice_channels = 0
        for channel in self.bot.get_all_channels():
            if isinstance(channel, discord.TextChannel):
                text_channels += 1
            if isinstance(channel, discord.VoiceChannel):
                voice_channels += 1
        await ctx.embed(title="Aoi Stats", fields=[
            ("Ping", f"{round(self.bot.latency*1000)}ms"),
            ("Presence", f"{len(self.bot.guilds)} Guilds\n"
                         f"{text_channels} Text Channels\n"
                         f"{voice_channels} Voice Channels\n")
        ])


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Aoi(bot))
