import discord
from discord.ext import commands
import aoi
import aiohttp

class Aoi(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands having to do with the bot herself"

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

    @commands.command(brief="Gives a link to invite Aoi to your server")
    async def invite(self, ctx: aoi.AoiContext):
        permissions_int = 84992
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=" \
                     f"{permissions_int}&scope=bot"
        await ctx.send_info(f"Invite me to your server [here]({invite_url})")

    @commands.command(
        brief="Shows Aoi's latency to discord"
    )
    async def ping(self, ctx: aoi.AoiContext):
        await ctx.send_info(f":ping_pong: {round(self.bot.latency*1000)}ms")

    @commands.is_owner()
    @commands.command(
        brief="Log AOI out"
    )
    async def die(self, ctx: aoi.AoiContext):
        await self.bot.db.close()
        await self.bot.logout()


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Aoi(bot))
