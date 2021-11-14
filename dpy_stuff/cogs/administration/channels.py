from datetime import timedelta
from typing import Dict

import discord
from discord.ext import commands

from aoi import bot
from aoi.libs.conversions import dhms_notation, hms_notation
from aoi.libs.converters import t_delta


class Channels(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @property
    def slowmodes(self) -> Dict[int, int]:
        return self.bot.slowmodes

    async def _init(self):
        await self.bot.wait_until_ready()
        for row in await self.bot.db.conn.execute_fetchall("select * from slowmode"):
            self.slowmodes[row[0]] = row[1]

        # update slowmodes
        ch: discord.TextChannel
        for channel, value in self.slowmodes.items():
            ch = self.bot.get_channel(channel)
            if not ch:
                # channel doesn't exist anymore
                del self.slowmodes[channel]
                await self.bot.db.conn.execute("delete from slowmode where channel=?", (channel,))
                await self.bot.db.conn.execute("delete from last_messages where channel=?", (channel,))
            if ch.slowmode_delay < 6 * 3600:
                # slowmode is less than 6 hours, so Aoi no longer needs to handle it
                await self.bot.db.conn.execute("delete from slowmode where channel=?", (channel,))
                await self.bot.db.conn.execute("delete from last_messages where channel=?", (channel,))
        await self.bot.db.conn.commit()  # commit transaction once done

    @property
    def description(self):
        return "Commands dealing with channels"

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True)
    @commands.command(brief="Toggles if a channel is NSFW. Defaults to the current channel")
    async def nsfw(self, ctx: bot.AoiContext, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        await channel.edit(nsfw=not channel.nsfw)
        await ctx.send_ok(f"{channel.mention} has been marked as {'' if channel.nsfw else 'not '} NSFW.")

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True)
    @commands.command(
        brief="Change slowmode on the current channel. 0 to clear.",
        aliases=["slmd"],
        description="""
        slowmode 3s
        slowmode 0
        """,
    )
    async def slowmode(self, ctx: bot.AoiContext, time: t_delta()):
        time: timedelta = time
        if time.seconds < 0:
            return await ctx.send_error("Invalid slowmode time")
        if not time.days and time.seconds <= 21600:
            if ctx.channel.id in self.slowmodes:
                del self.slowmodes[ctx.channel.id]
                await self.bot.db.conn.execute("delete from slowmode where channel=?", (ctx.channel.id,))
                await self.bot.db.conn.execute("delete from last_messages where channel=?", (ctx.channel.id,))
                await self.bot.db.conn.commit()
            await ctx.channel.edit(slowmode_delay=time.seconds)
            return await ctx.send_ok(
                f"Slowmode set to {hms_notation(time.seconds)}" if time.total_seconds() else "Slowmode turned off."
            )
        await ctx.channel.edit(slowmode_delay=21600)
        await self.bot.db.conn.execute("delete from slowmode where channel=?", (ctx.channel.id,))
        await self.bot.db.conn.execute(
            "insert into slowmode values (?,?)",
            (ctx.channel.id, int(time.total_seconds())),
        )
        await self.bot.db.conn.commit()
        self.slowmodes[ctx.channel.id] = int(time.total_seconds())
        await ctx.send_ok(f"Slowmode set to {dhms_notation(time)}" if time.total_seconds() else "Slowmode turned off")

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True, manage_permissions=True)
    @commands.command(
        brief="Attempts to reverse a member-level lockout/lockin. Defaults to the current channel.",
        aliases=["unlockout", "unlockin", "lockrem"],
    )
    async def remlock(
        self,
        ctx: bot.AoiContext,
        member: discord.Member,
        channel: discord.TextChannel = None,
    ):
        channel = channel or ctx.channel
        previous = channel.permissions_for(member).read_messages
        await channel.set_permissions(member, read_messages=None)
        now = channel.permissions_for(member).read_messages
        await ctx.send_ok(
            f"Lock for {member.mention} in {channel.mention} removed. "
            + (
                f"The user still can{'' if now else 'not'} see this channel. You can force the user to "
                f"{'not ' if now else ''}see this channel with `{ctx.prefix}lock{'out' if now else 'in'}"
                f" @{member.name} #{channel.name}.`"
                if (now == previous)
                else ""
            )
        )

    @commands.cooldown(rate=1, per=30, type=commands.BucketType.member)
    @commands.has_permissions(manage_channels=True, manage_permissions=True)
    @commands.command(brief="Attempts to force to let a user see a channel. Defaults to the current channel.")
    async def lockin(
        self,
        ctx: bot.AoiContext,
        member: discord.Member,
        channel: discord.TextChannel = None,
    ):
        channel = channel or ctx.channel
        await channel.set_permissions(member, read_messages=True)
        await ctx.send_ok(
            f"{member.mention} forcefully allowed into {channel.mention}. You can reverse this with "
            f"`{ctx.prefix}unlockout @{member.name} #{channel.name}`."
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        # remove Aoi-enforced slowmode when the channel slowmode is manually changed to something
        # under 6 hours
        if (
            not isinstance(before, discord.TextChannel)
            or not isinstance(after, discord.TextChannel)
            or before.slowmode_delay == after.slowmode_delay
        ):
            # the 2nd isinstance here is needed so the linter doesn't complain about the
            # following slowmode check
            return
        if after.slowmode_delay < 21600:
            if after.id in self.slowmodes:
                del self.slowmodes[after.id]
                await self.bot.db.conn.execute("delete from slowmode where channel=?", (after.id,))
                await self.bot.db.conn.execute("delete from last_messages where channel=?", (after.id,))
                await self.bot.db.conn.commit()


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(Channels(bot))
