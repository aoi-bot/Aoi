import discord
from discord.ext import commands
import aoi
import aiohttp

class Aoi(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.command(
        brief="Shows bot stats"
    )
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

    @commands.is_owner()
    @commands.command(
        brief="Set's the bot's avatar",
        aliases=["setav"]
    )
    async def setavatar(self, ctx: aoi.AoiContext, *, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url) as resp:
                try:
                    await self.bot.user.edit(avatar=await resp.read())
                except discord.HTTPException as err:
                    if err.status == 429:
                        await ctx.send_error("You're editing your avatar too fast!")
                    else:
                        await ctx.send_error("An error occurred while changing my avatar.")
                except discord.InvalidArgument:
                    await ctx.send_error("Invalid image format.")
                else:
                    await ctx.send_ok("Avatar changed!")



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Aoi(bot))
