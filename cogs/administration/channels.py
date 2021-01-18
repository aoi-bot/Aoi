from datetime import timedelta

import aoi
import discord
from discord.ext import commands
from libs.conversions import hms_notation
from libs.converters import t_delta


class Channels(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands dealing with channels"

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True)
    @commands.command(
        brief="Toggles if a channel is NSFW"
    )
    async def nsfw(self, ctx: aoi.AoiContext, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.edit(nsfw=not channel.nsfw)
        await ctx.send_ok(f"{channel.mention} has been marked as {'' if channel.nsfw else 'not '} NSFW.")

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True)
    @commands.command(
        brief="Change slowmode on a channel",
        aliases=["slmd"]
    )
    async def slowmode(self, ctx: aoi.AoiContext, time: t_delta(), channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        time: timedelta = time
        if time.days or time.seconds > 21600 or time.seconds < 0:
            return await ctx.send_error("Invalid slowmode time")
        await channel.edit(slowmode_delay=time.seconds)
        await ctx.send_ok(f"Slowmode on {channel.mention} set to {hms_notation(time.seconds)}" if time.seconds else "Slowmode turned off.") # noqa

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(
        manage_channels=True,
        manage_permissions=True
    )
    @commands.command(
        brief="Mutes a user in a channel"
    )
    async def chanmute(self, ctx: aoi.AoiContext, member: discord.Member, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.set_permissions(member, send_messages=False)
        await ctx.send_ok(f"{member.mention} muted in {channel.mention}")

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(
        manage_channels=True,
        manage_permissions=True
    )
    @commands.command(
        brief="Attempts to unmute a user in a channel",
        aliases=["unchanmute"]
    )
    async def remchanmute(self, ctx: aoi.AoiContext, member: discord.Member, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        previous = channel.permissions_for(member).send_messages
        await channel.set_permissions(member, send_messages=None)
        now = channel.permissions_for(member).send_messages
        await ctx.send_ok(f"Lock for {member.mention} in {channel.mention} removed. " +
                          (f"Nothing has changed. The user still can{'' if now else 'not'} talk in this channel." if
                           (now == previous)
                           else ""))

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
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

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(
        manage_channels=True,
        manage_permissions=True
    )
    @commands.command(
        brief="Attempts to reverse a member-level lockout/lockin",
        aliases=["unlockout", "unlockin", "lockrem"]
    )
    async def remlock(self, ctx: aoi.AoiContext, member: discord.Member, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        previous = channel.permissions_for(member).read_messages
        await channel.set_permissions(member, read_messages=None)
        now = channel.permissions_for(member).read_messages
        await ctx.send_ok(f"Lock for {member.mention} in {channel.mention} removed. " +
                          (f"The user still can{'' if now else 'not'} see this channel. You can force the user to "
                           f"{'not ' if now else ''}see this channel with `{ctx.prefix}lock{'out' if now else 'in'}"
                           f" @{member.name} #{channel.name}.`" if
                           (now == previous)
                           else ""))

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
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
    bot.add_cog(Channels(bot))
