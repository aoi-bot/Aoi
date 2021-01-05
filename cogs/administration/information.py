from typing import List, Union, Optional

import aoi
import discord
from discord.ext import commands
from libs import conversions


class Information(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Get information about parts of your server"

    @commands.guild_only()
    @commands.command(brief="Shows info on a channel, role, member, emoji, or message")
    async def info(self, ctx: aoi.AoiContext,  # noqa: C901
                   obj: Union[
                       discord.Role,
                       discord.TextChannel,
                       discord.Message,
                       discord.VoiceChannel,
                       discord.Member,
                       discord.Emoji,
                       discord.PartialEmoji
                   ]
                   ):
        if isinstance(obj, discord.Role):
            if obj.id in [r.id for r in ctx.guild.roles]:
                return await self.roleinfo(ctx, obj)
            else:
                raise commands.BadArgument("Role not in server")
        if isinstance(obj, discord.Member):
            return await self.userinfo(ctx, obj)
        if isinstance(obj, discord.VoiceChannel):
            if obj.id in [vc.id for vc in ctx.guild.voice_channels]:
                return await self.voiceinfo(ctx, channel=obj)
            else:
                raise commands.BadArgument("Channel not in server")
        if isinstance(obj, discord.TextChannel):
            if obj.id in [tc.id for tc in ctx.guild.text_channels]:
                return await self.textinfo(ctx, channel=obj)
            else:
                raise commands.BadArgument("Channel not in server")
        if isinstance(obj, discord.Message):
            chan: discord.TextChannel = obj.channel
            author: discord.Member = obj.author
            if chan.guild.id not in [tc.id for tc in ctx.guild.text_channels]:
                raise commands.BadArgument("Message not in server")
            return await ctx.embed(
                title=f"Info for message",
                fields=[
                    ("ID", obj.id),
                    ("Channel", f"{chan} | {chan.mention}"),
                    ("Author", f"{author} | {author.mention}"),
                    ("Sent at", obj.created_at.strftime('%c'))
                ]
            )
        if isinstance(obj, (discord.Emoji, discord.PartialEmoji)):
            return await self.emojiinfo(ctx, obj)

    @commands.command(brief="Shows info on a user", aliases=["uinfo"])
    async def userinfo(self, ctx: aoi.AoiContext, member: discord.Member = None):
        if not member:
            member = ctx.author
        joined_at = member.joined_at.strftime("%c")
        created_at = member.created_at.strftime("%c")
        r: discord.Role
        hoisted_roles = [r for r in member.roles if r.hoist and r.id != ctx.guild.id]
        normal_roles = [r for r in member.roles if not r.hoist and r.id != ctx.guild.id]
        await ctx.embed(
            title=f"Info for {member}",
            fields=[
                ("ID", member.id),
                ("Joined Server", joined_at),
                ("Joined Discord", created_at),
                (f"Hoisted Roles ({len(hoisted_roles)}) ",
                 " ".join([r.mention for r in hoisted_roles[:-6:-1]]) if hoisted_roles
                 else "None"),
                (f"Normal Roles ({len(normal_roles)})",
                 " ".join([r.mention for r in normal_roles[:-6:-1] if r.id not in
                           [x.id for x in hoisted_roles]]) if len(normal_roles) > 1
                 else "None"),
                ("Top Role", member.roles[-1].mention if len(member.roles) > 1 else "None"),
                ("Ansura Profile", f"https://www.ansura.xyz/profile/{member.id}")
            ],
            clr=member.color,
            thumbnail=member.avatar_url
        )

    @commands.command(brief="Shows info on the current server", aliases=["sinfo"])
    async def serverinfo(self, ctx: aoi.AoiContext):
        guild: discord.Guild = ctx.guild
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
                ("Owner", guild.owner),
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
            thumbnail=guild.icon_url,
            footer=f"Do `{ctx.prefix}emojis` to show server emojis."
        )

    @commands.command(brief="Shows info on a role", aliases=["rinfo"])
    async def roleinfo(self, ctx: aoi.AoiContext, role: discord.Role):
        await ctx.embed(
            clr=role.colour,
            title=f"Info for {role}",
            fields=[
                ("ID", role.id),
                ("Members", len(role.members)),
                ("Color", conversions.color_to_string(role.colour)),
                ("Hoisted", role.hoist),
                ("Mentionable", role.mentionable),
                ("Position", role.position),
                ("Created at", role.created_at.strftime("%c"))
            ]
        )

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Shows mentionable roles")
    async def menroles(self, ctx: aoi.AoiContext):
        r: discord.Role
        roles: List[discord.Role] = [r for r in ctx.guild.roles if r.mentionable]
        await ctx.send_info(" ".join(r.mention for r in roles)
                            if roles else "None", title="Mentionable Roles")

    @commands.command(brief="Shows info on a voice channel", aliases=["vinfo"])
    async def voiceinfo(self, ctx: aoi.AoiContext, *, channel: discord.VoiceChannel):
        await ctx.embed(
            title=f"Info for {channel}",
            fields=[
                ("ID", channel.id),
                ("Created at", channel.created_at.strftime("%c")),
                ("Max Users", channel.user_limit or "No Limit"),
                ("Bitrate", f"{channel.bitrate // 1000}kbps"),
            ]
        )

    @commands.command(brief="Shows info on a text channel", aliases=["tcinfo"])
    async def textinfo(self, ctx: aoi.AoiContext, *, channel: discord.TextChannel):
        await ctx.embed(
            title=f"Info for {channel}",
            fields=[
                ("ID", channel.id),
                ("Created at", channel.created_at.strftime("%c")),
                ("Slowmode", f"{channel.slowmode_delay}s" if channel.slowmode_delay else "No Slowmode")
            ]
        )

    @commands.command(
        brief="Shows info on an emoji",
        aliases=["einfo"]
    )
    async def emojiinfo(self, ctx: aoi.AoiContext, emoji: Union[discord.Emoji, discord.PartialEmoji]):
        def _(typ):
            return f"https://cdn.discordapp.com/emojis/{emoji.id}.{typ}?v=1"

        if isinstance(emoji, discord.PartialEmoji) and \
                (not emoji.is_custom_emoji() or emoji.is_unicode_emoji()):
            return await ctx.send_error("Emoji must be a custom emoji")
        await ctx.embed(
            title=f"Info for {emoji}",
            fields=[
                ("ID", emoji.id),
                ("Name", emoji.name),
                ("Animated", emoji.animated),
                ("Links", f"[jpeg]({_('jpeg')}) "
                          f"[png]({_('png')}) "
                          f"[gif]({_('gif')}) "
                          f"[webp]({_('webp')}) "),
                ("Usage", f"\\<{'a' if emoji.animated else ''}\\:{emoji.name}:{emoji.id}>")
            ],
            not_inline=[3, 4],
            thumbnail=_("gif")
        )

    @commands.command(
        brief="Shows the server's emojis"
    )
    async def emojis(self, ctx: aoi.AoiContext):
        if not ctx.guild.emojis:
            return await ctx.send_info("Server has no emojis")
        await ctx.paginate(
            lst=[f"{str(e)} | {e.name} | {e.id}" for e in ctx.guild.emojis],
            n=20,
            title=f"{ctx.guild}'s emojis",
            numbered=False
        )

    @commands.command(
        brief="Shows your or a member's permissions in a channel",
        aliases=["perms"]
    )
    async def permissions(self, ctx: aoi.AoiContext,
                          member: Optional[discord.Member] = None,
                          channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]] = None):
        channel = channel or ctx.channel
        member = member or ctx.author
        perms = member.permissions_in(channel)
        await ctx.embed(
            title=f"Permissions for {member} in {channel}",
            thumbnail=member.avatar_url,
            description="```diff\n" +
                        "\n".join(
                            f"{'+' if perm[1] or perms.administrator else '-'} "
                            f"{conversions.camel_to_title(perm[0])}"
                            for perm in perms
                        ) + "```"
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Information(bot))
