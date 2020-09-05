from datetime import datetime

import discord
from discord.ext import commands

import aoi
from libs.conversions import dhm_notation


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
        await ctx.embed(author=f"Aoi {self.bot.version}",
                        fields=[
                            ("Ping", f"{round(self.bot.latency * 1000)}ms"),
                            ("Messages", f"{self.bot.messages}"),
                            ("Commands\nExecuted", f"{self.bot.commands_executed}"),
                            ("Uptime", dhm_notation(datetime.now() - self.bot.start_time)),
                            ("Presence", f"{len(self.bot.guilds)} Guilds\n"
                                         f"{text_channels} Text Channels\n"
                                         f"{voice_channels} Voice Channels\n"),
                        ],
                        thumbnail=self.bot.user.avatar_url)

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
        await ctx.send_info(f":ping_pong: {round(self.bot.latency * 1000)}ms")

    @commands.is_owner()
    @commands.command(
        brief="Log AOI out"
    )
    async def die(self, ctx: aoi.AoiContext):
        await self.bot.db.close()
        await self.bot.logout()

    @commands.is_owner()
    @commands.command(
        brief="Flush XP/Currency to database manually"
    )
    async def flush(self, ctx: aoi.AoiContext):
        await self.bot.db.cache_flush()
        await ctx.send_ok("Cache flushed to disk")

    @commands.is_owner()
    @commands.command(
        brief="List servers this server is part of"
    )
    async def guildlist(self, ctx: aoi.AoiContext):
        await ctx.paginate(
            [f"{g.id}\n{g.name}\n" for g in self.bot.guilds],
            title="Servers Aoi is in",
            n=5
        )

    @commands.is_owner()
    @commands.command(
        brief="Basic information about a server the bot is on"
    )
    async def guildinfo(self, ctx: aoi.AoiContext, guild: int):
        guild: discord.Guild = self.bot.get_guild(guild)
        if not guild:
            return await ctx.send_error("Im'm not in a guild with that ID")
        created = guild.created_at.strftime("%c")
        voice_channels = len(guild.voice_channels)
        text_channels = len(guild.text_channels)
        roles = len(guild.roles) - 1
        statuses = {
            "dnd": 0,
            "idle": 0,
            "online": 0,
            "bot": 0,
            "offline": 0
        }
        m: discord.Member
        for m in guild.members:
            if m.bot:
                statuses["bot"] += 1
            else:
                statuses[str(m.status)] += 1
        await ctx.embed(
            title=f"Info for {guild}",
            fields=[
                ("ID", guild.id),
                ("Created at", created),
                ("Channels", f"{voice_channels} Voice, {text_channels} Text"),
                ("System Channel", (guild.system_channel.mention if guild.system_channel else "None")),
                ("Members", guild.member_count),
                ("Roles", roles),
                ("Region", guild.region),
                ("Features", "\n".join(guild.features) if guild.features else "None"),
                ("Breakdown", f":green_circle: {statuses['online']} online\n"
                              f":yellow_circle: {statuses['idle']} idle\n"
                              f":red_circle: {statuses['dnd']} dnd\n"
                              f":white_circle: {statuses['offline']} offline\n"
                              f":robot: {statuses['bot']} bots\n")
            ],
            thumbnail=guild.icon_url
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Aoi(bot))
