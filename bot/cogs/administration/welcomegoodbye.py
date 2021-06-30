from typing import Optional, Union

from bot import aoi
import discord
from bot.cog_helpers.admin import AdminService
from discord.ext import commands


# TODO help refactor

class WelcomeGoodbye(AdminService, commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        super().__init__(bot.config.get("api.port"))
        self.bot = bot

    @property
    def description(self):
        return "Set and view the welcome and goodbye messages of a server"

    @commands.command(
        brief="Shows the welcome message for a server"
    )
    async def showjoin(self, ctx: aoi.AoiContext):
        message = await self.get_welcome_message(ctx.guild.id)
        await ctx.embed(
            description=discord.utils.escape_markdown(message.message),
            fields=[
                ("Channel", f"<#{message.channel}>" if message.channel else "Not enabled"),
                ("Delete after", f"{message.delete}s" if message.delete else "Never")
            ]
        )

    @commands.command(
        brief="Shows the leave message for a server"
    )
    async def showleave(self, ctx: aoi.AoiContext):
        message = await self.get_goodbye_message(ctx.guild.id)
        await ctx.embed(
            description=discord.utils.escape_markdown(message.message),
            fields=[
                ("Channel", f"<#{message.channel}>" if message.channel else "Not enabled"),
                ("Delete after", f"{message.delete}s" if message.delete else "Never")
            ]
        )

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Set the goodbye message for a server"
    )
    async def leavemsg(self, ctx: aoi.AoiContext, *, message: str):
        await self.set_goodbye_message(ctx.guild.id, message=message)
        await ctx.send_ok("Leave message set")

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Set the channel the goodbye message displays in"
    )
    async def leavemsgchnl(self, ctx: aoi.AoiContext, channel: Optional[Union[discord.TextChannel, str]]):
        if isinstance(channel, str):
            if channel.lower() == "off":
                await self.set_goodbye_message(ctx.guild.id, channel=None)
                return await ctx.send_ok("Leave message turned off")
            raise commands.BadArgument(f"Usage: `{ctx.prefix}leavemsgchnl #channel` | "
                                       f"`{ctx.prefix}leavemsgchnl off` | `{ctx.prefix}leavemsgchnl")
        if not channel:
            message = await self.get_goodbye_message(ctx.guild.id)
            return await ctx.send_ok(f"Leave message is enabled on <#{message.channel}>")
        await self.set_goodbye_message(ctx.guild.id, channel=channel)
        return await ctx.send_ok(f"Leave message is enabled on {channel.mention}")

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Set the deletion delay for the leave message, 0 to disable"
    )
    async def leavemsgdel(self, ctx: aoi.AoiContext, secs: int):
        await self.set_goodbye_message(ctx.guild.id, delete_after=secs)
        await ctx.send_ok(f"Leave messages will {'never ' if not secs else ''}delete" +
                          (f" after {secs}s" if secs else ""))

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Set the welcome message for a server"
    )
    async def joinmsg(self, ctx: aoi.AoiContext, *, message: str):
        await self.set_welcome_message(ctx.guild.id, message=message)
        await ctx.send_ok("Join message set")

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Set the channel the welcome message displays in"
    )
    async def joinmsgchnl(self, ctx: aoi.AoiContext, channel: Optional[Union[discord.TextChannel, str]]):
        if isinstance(channel, str):
            if channel.lower() == "off":
                await self.set_welcome_message(ctx.guild.id, channel=None)
                return await ctx.send_ok("Join message turned off")
            raise commands.BadArgument(f"Usage: `{ctx.prefix}joinmsgchnl #channel` | "
                                       f"`{ctx.prefix}joinmsgchnl off` | `{ctx.prefix}joinmsgchnl")
        if not channel:
            message = await self.get_welcome_message(ctx.guild.id)
            return await ctx.send_ok(f"Join message is enabled on <#{message.channel}>")
        await self.set_welcome_message(ctx.guild.id, channel=channel)
        return await ctx.send_ok(f"Join message is enabled on {channel.mention}")

    @commands.has_permissions(manage_guild=True)
    @commands.command(
        brief="Set the deletion delay for the welcome message, 0 to disable"
    )
    async def joinmsgdel(self, ctx: aoi.AoiContext, secs: int):
        await self.set_welcome_message(ctx.guild.id, delete_after=secs)
        await ctx.send_ok(f"Join messages will {'never ' if not secs else ''}delete" +
                          (f" after {secs}s" if secs else ""))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        message = await self.get_welcome_message(member.guild.id)
        if message.channel:
            await self.bot.send_json_to_channel(message.channel, message.message, member=member,
                                                delete_after=message.delete if message.delete else None)
        if member.guild.id in self.bot.db.auto_roles:
            # remove invalid roles from the auto role list
            lost_roles = []
            for r in self.bot.db.auto_roles[member.guild.id]:
                if not member.guild.get_role(r):
                    lost_roles.append(r)
            if lost_roles:
                await member.trigger_typing()
            for r in lost_roles:
                await self.bot.db.del_auto_role(member.guild, r)

            if self.bot.db.auto_roles[member.guild.id]:
                await member.add_roles(*[
                    member.guild.get_role(r)
                    for r in self.bot.db.auto_roles[member.guild.id]
                ])

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        message = await self.get_goodbye_message(member.guild.id)
        if not message.channel:
            return
        await self.bot.send_json_to_channel(message.channel, message.message, member=member,
                                            delete_after=message.delete if message.delete else None)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(WelcomeGoodbye(bot))
