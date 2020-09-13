from datetime import timedelta
from typing import Union

import aiohttp
import discord
from discord.ext import commands

import aoi
from libs.conversions import hms_notation
from libs.converters import t_delta


class Guilds(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands for managing servers"

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["guildnm", "servernm"],
                      brief="Renames the server")
    async def renameserver(self, ctx: aoi.AoiContext, *, name: str):
        await ctx.confirm_coro(f"Rename server to `{name}`?",
                               f"Server renamed to `{name}`",
                               "Server rename cancelled",
                               ctx.guild.edit(name=name))

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["guildav", "serverav", "servericon"],
                      brief="Sets the server's icon")
    async def serveravatar(self, ctx: aoi.AoiContext, *, url: str):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                await ctx.confirm_coro("Change guild avatar?",
                                       "Avatar changed",
                                       "Avatar change cancelled",
                                       ctx.guild.edit(
                                           icon=await resp.content.read()
                                       ))

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["guildreg", "serverreg"],
                      brief="Sets the server's voice region")
    async def serverregion(self, ctx: aoi.AoiContext, *, region: str):
        region = region.lower().replace(" ", "-").replace("_", "-")
        if region not in map(str, discord.VoiceRegion):
            raise commands.BadArgument(f"Region `{region}` invalid. Do `{ctx.prefix}regions` "
                                       f"to view a list of supported regions")
        reg = discord.VoiceRegion.try_value(region)
        await ctx.confirm_coro(f"Set server region to `{reg}`?",
                               f"Set to `{reg}`",
                               "Server region change cancelled",
                               ctx.guild.edit(region=reg))

    @commands.command(
        brief="List of regions the server can use"
    )
    async def regions(self, ctx: aoi.AoiContext):
        await ctx.send_info(" ".join(map(str, discord.VoiceRegion)),
                            title="Voice Regions")

    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_permissions(manage_emojis=True)
    @commands.command(
        brief="Deletes up to 10 emojis",
        aliases=["de"]
    )
    async def delemoji(self, ctx: aoi.AoiContext, emojis: commands.Greedy[Union[discord.Emoji, discord.PartialEmoji]]):
        e: discord.Emoji
        if len(emojis) < 1:
            raise commands.BadArgument("Must send an emoji")
        if len(emojis) > 10:
            raise commands.BadArgument("Must be less than 10 emojis")
        for e in emojis:
            if isinstance(e, discord.PartialEmoji) or e.guild_id != ctx.guild.id:
                return await ctx.send_error(f"{e} is not from this server. This command can only be used with emojis "
                                            f"that belong to this server.")

        async def _del():
            _e: discord.Emoji
            for _e in emojis:
                await _e.delete(reason=f"Bulk delete | {ctx.author} | {ctx.author.id}")

        await ctx.confirm_coro(
            "Delete " + " ".join(map(str, emojis)) + "?",
            "Emojis deleted",
            "Emoji deletion cancelled",
            _del()
        )

    @commands.cooldown(rate=1, per=60, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True)
    @commands.command(
        brief="Toggles if a channel is NSFW"
    )
    async def nsfw(self, ctx: aoi.AoiContext, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.edit(nsfw=not channel.nsfw)
        await ctx.send_ok(f"{channel.mention} has been marked as {'' if channel.nsfw else 'not '} NSFW.")

    @commands.cooldown(rate=1, per=60, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True)
    @commands.command(
        brief="Change slowmode on a channel",
        aliases=["slmd"]
    )
    async def slowmode(self, ctx: aoi.AoiContext, time: t_delta()):
        time: timedelta = time
        if time.days or time.seconds > 21600 or time.seconds < 0:
            return await ctx.send_error("Invalid slowmode time")
        await ctx.channel.edit(slowmode_delay=time.seconds)
        await ctx.send_ok(f"Slowmode set to {hms_notation(time.seconds)}" if time.seconds else "Slowmode turned off.")

    #@commands.cooldown(rate=1, per=60, type=commands.BucketType.member)
    @commands.has_permissions(
        manage_channels=True,
        manage_permissions=True
    )
    @commands.command(
        brief="Attempts to lock a user out of a channel"
    )
    async def lockout(self, ctx: aoi.AoiContext, member: discord.Member, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(member, read_messages=False)
        await ctx.send_ok(f"{member.mention} locked out of {channel.mention}")

    #@commands.cooldown(rate=1, per=60, type=commands.BucketType.member)
    @commands.has_permissions(
        manage_channels=True,
        manage_permissions=True
    )
    @commands.command(
        brief="Attempts to reverse a member-level lockout/lockin",
        aliases=["unlockout","unlockin","lockrem"]
    )
    async def remlock(self, ctx: aoi.AoiContext, member: discord.Member, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        previous = channel.permissions_for(member).read_messages
        await channel.set_permissions(member, read_messages=None)
        await ctx.send_ok(f"Lockout for {member.mention} in {channel.mention} removed." +
                          (f"They still cannot see this channel, due to another permission overwrite not set by Aoi. "
                           f"If you were trying to allow them to view a "
                           f"channel, either change the offending overwrite, or use "
                           f"`{ctx.prefix}lockin @{member.name} #{channel.name}` "
                           f"to force a user to be able to see this channel." if
                           (not channel.permissions_for(member).read_messages and not previous)
                           else ""))

    #@commands.cooldown(rate=1, per=60, type=commands.BucketType.member)
    @commands.has_permissions(
        manage_channels=True,
        manage_permissions=True
    )
    @commands.command(
        brief="Attempts to force to let a user see a channel"
    )
    async def lockin(self, ctx: aoi.AoiContext, member: discord.Member, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(member, read_messages=True)
        await ctx.send_ok(f"{member.mention} forcefully allowed into {channel.mention}. You can reverse this with "
                          f"`{ctx.prefix}unlockout @{member.name} #{channel.name}`.")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Guilds(bot))
