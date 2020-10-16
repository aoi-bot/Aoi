import asyncio
from datetime import timedelta

import discord
from discord.ext import commands

import aoi
from libs.conversions import hms_notation
from libs.converters import t_delta


class Channels(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands dealing with channels"

    @commands.cooldown(rate=1, per=300, type=commands.BucketType.guild)
    @commands.has_permissions(
        manage_guild=True,
        manage_channels=True
    )
    @commands.max_concurrency(number=1, per=commands.BucketType.guild)
    @commands.command(brief="Names channels according to a pattern")
    async def namechannels(self, ctx: aoi.AoiContext):  # noqa: C901
        raise commands.DisabledCommand()
        await ctx.send_info("Input the format you want to use for categories, where `text` is the channel name, "
                            "or `cancel` to stop")
        cat_pattern = await ctx.input(typ=str, ch=lambda s: "text" in s, timeout=120.0)
        if not cat_pattern:
            return await ctx.send_ok("Cancelled")
        await ctx.send_info("Input the format you want to use for channels in a category, "
                            "where `text` is the channel name, or `cancel` to stop")
        channel_pattern = await ctx.input(typ=str, ch=lambda s: "text" in s, timeout=120.0)
        if not channel_pattern:
            return await ctx.send_ok("Cancelled")

        await ctx.send_info("Input the format you want to use for channels not in a category, where `text` is the "
                            "channel name, `same` to use the previous value, or `cancel` to stop.")
        channel_alone_pattern = await ctx.input(typ=str, ch=lambda s: "text" in s or s.lower() == "same")
        if not channel_alone_pattern:
            return await ctx.send_ok("Cancelled")
        if channel_alone_pattern.lower() == "same":
            channel_alone_pattern = channel_pattern

        await ctx.send_info("Input the format you want to use for the first channels in a category, where `text` is "
                            "the channel name, `same` to use the default channel pattern, or `cancel` to stop.")
        channel_f_pattern = await ctx.input(typ=str, ch=lambda s: "text" in s or s.lower() == "same")
        if not channel_f_pattern:
            return await ctx.send_ok("Cancelled")
        if channel_f_pattern.lower() == "same":
            channel_f_pattern = channel_pattern

        await ctx.send_info("Input the format you want to use for the last channels in a category, where `text` is "
                            "the channel name, `same` to use the default channel pattern, or `cancel` to stop.")
        channel_l_pattern = await ctx.input(typ=str, ch=lambda s: "text" in s or s.lower() == "same")
        if not channel_l_pattern:
            return await ctx.send_ok("Cancelled")
        if channel_l_pattern.lower() == "same":
            channel_l_pattern = channel_pattern

        await ctx.send_info("Input the format you want to use for the voice channels, where `text` is "
                            "the channel name, `same` to use the default channel pattern, or `cancel` to stop.")
        channel_v_pattern = await ctx.input(typ=str, ch=lambda s: "text" in s or s.lower() == "same")
        if not channel_v_pattern:
            return await ctx.send_ok("Cancelled")
        if channel_v_pattern.lower() == "same":
            channel_v_pattern = channel_pattern

        cat: discord.CategoryChannel
        channel: discord.TextChannel
        v_channel: discord.VoiceChannel
        guild: discord.Guild = ctx.guild

        async def do_op():
            nonlocal cat
            nonlocal channel
            nonlocal v_channel
            for cat in guild.categories:
                for channel in cat.text_channels[1:-1]:
                    await channel.edit(name=channel_pattern.replace("text", channel.name))
                    await asyncio.sleep(0.5)
                await cat.text_channels[0].edit(name=channel_f_pattern.replace("text", channel.name))
                await asyncio.sleep(0.5)
                await cat.text_channels[-1].edit(name=channel_l_pattern.replace("text", channel.name))
                await asyncio.sleep(0.5)
            for channel in guild.voice_channels:
                await channel.edit(name=channel_v_pattern.replace("text", channel.name))
                await asyncio.sleep(0.5)
            for channel in guild.text_channels:
                if not channel.category:
                    await channel.edit(name=channel_alone_pattern.replace("text", channel.name))
                    await asyncio.sleep(0.5)

        task = self.bot.create_task(ctx, do_op())
        await task

        await ctx.send(f"{ctx.author.mention} Done!")

    @commands.cooldown(rate=1, per=300, type=commands.BucketType.guild)
    @commands.has_permissions(
        manage_guild=True,
        manage_channels=True
    )
    @commands.command(
        brief="Remove text from the beginning or end of a channel. Separate multiple things to remove with a semicolon"
    )
    async def stripchannels(self, ctx: aoi.AoiContext, text: str):
        raise commands.DisabledCommand()
        lst = text.split(";")

        async def strip_ends(s: str):
            for r in lst:
                while s.startswith(r) or s.endswith(r):
                    if s.startswith(r):
                        s = s[len(r):]
                    if s.endswith(r):
                        s = s[:-len(r)]
                    s = s.strip()
            return s

        async def do_op():
            for channel in ctx.guild.channels:
                await channel.edit(name=await strip_ends(channel.name))
                await asyncio.sleep(1)

        await ctx.send_info(f"Removing text from both ends of {len(ctx.guild.channels)} channel names. This will "
                            f"take at least {len(ctx.guild.channels)}s")
        await self.bot.create_task(ctx, do_op())
        await ctx.send_ok("Done!", ping=True)

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
    async def slowmode(self, ctx: aoi.AoiContext, time: t_delta()):
        time: timedelta = time
        if time.days or time.seconds > 21600 or time.seconds < 0:
            return await ctx.send_error("Invalid slowmode time")
        await ctx.channel.edit(slowmode_delay=time.seconds)
        await ctx.send_ok(f"Slowmode set to {hms_notation(time.seconds)}" if time.seconds else "Slowmode turned off.")

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
