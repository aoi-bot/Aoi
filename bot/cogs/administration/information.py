from typing import List, Union, Optional, Dict

from bot import aoi
import discord
from discord.ext import commands
from libs import conversions, misc as m


class Information(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Get information about parts of your server"

    @commands.guild_only()
    @commands.command(brief="Shows info on a channel, role, member, emoji, or message",
                      description="""
                      info @Role of Gamers
                      info #general
                      info General VC
                      info https://discord.com/channels/213/12312/712129
                      info :emoji:
                      info @member
                      """
                      )
    async def info(self, ctx: aoi.AoiContext, *,  # noqa: C901
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
            channel: discord.TextChannel = obj.channel
            author: discord.Member = obj.author
            if channel.id not in [tc.id for tc in ctx.guild.text_channels]:
                raise commands.BadArgument("Message not in server")
            return await ctx.embed(
                title=f"Info for message",
                fields=[
                    ("ID", obj.id),
                    ("Channel", f"{channel} | {channel.mention}"),
                    ("Author", f"{author} | {author.mention}"),
                    ("Sent at", obj.created_at.strftime('%c'))
                ]
            )
        if isinstance(obj, (discord.Emoji, discord.PartialEmoji)):
            return await self.emojiinfo(ctx, obj)

    @commands.command(brief="Shows a user's avatar. Defaults to showing your own.", aliases=["av", "pfp"])
    async def avatar(self, ctx: aoi.AoiContext, member: Optional[discord.Member] = None):
        member = member or ctx.author
        await ctx.embed(
            image=member.avatar.url,
            title=f"{member}'s avatar",
            description=f"{member.avatar.url}"
        )

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
            thumbnail=member.avatar.url)

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
        member: discord.Member
        for member in guild.members:
            if member.bot:
                statuses["bot"] += 1
            else:
                statuses[str(member.status)] += 1
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
            thumbnail=(guild.icon.url if guild.icon else None),
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
        brief="Shows your or a member's permissions in a channel. Defaults to the current channel.",
        aliases=["perms"]
    )
    async def permissions(self, ctx: aoi.AoiContext,
                          member: Optional[discord.Member] = None,
                          channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]] = None):
        channel = channel or ctx.channel
        member = member or ctx.author
        perms = channel.permissions_for(member)
        await ctx.embed(
            title=f"Permissions for {member} in {channel}",
            thumbnail=member.avatar.url,
            description="```diff\n" +
                        "\n".join(
                            f"{'+' if perm[1] or perms.administrator else '-'} "
                            f"{conversions.camel_to_title(perm[0])}"
                            for perm in perms
                        ) + "```"
        )

    @commands.command(
        brief="Shows a role's permissions, optionally in a channel. Defaults to showing the role's server-wide "
              "permissions",
        aliases=["rperms", "roleperms"]
    )
    async def rolepermissions(self, ctx: aoi.AoiContext, role: Union[discord.Role, str],
                              channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]] = None):
        if isinstance(role, str):
            if role == "@everyone" or role == "everyone":
                role = ctx.guild.get_role(ctx.guild.id)
            else:
                raise commands.RoleNotFound(role)

        def _(perm, ov):
            if ov.administrator:
                return True
            if perm[1] is False:
                return "-"
            if perm[1] is None:
                return "#"
            return "+"

        if not channel:
            # grab guild-level settings
            perms = role.permissions
            return await ctx.embed(
                title=f"Server permissions for {role}",
                description="```diff\n" +
                            "\n".join(
                                f"{'+' if perm[1] or perms.administrator else '-'} "
                                f"{conversions.camel_to_title(perm[0])}"
                                for perm in perms
                            ) + "```"
            )
        overwrite: discord.PermissionOverwrite = channel.overwrites_for(role)
        if not overwrite:
            return await ctx.send_info(f"No permission overwrites in {channel} for {role}")
        return await ctx.embed(
            title=f"Permission overwrite for {role} in {channel}",
            description="```diff\n" +
                        "\n".join(
                            f"{_(perm, overwrite)} "
                            f"{conversions.camel_to_title(perm[0])}"
                            for perm in overwrite
                        ) + "```"
        )

    @commands.command(
        brief="Shows people in a role"
    )
    async def hasrole(self, ctx: aoi.AoiContext, *, role: discord.Role):
        await ctx.paginate(
            [f"{user.mention} - {user.id} - {user}" for user in role.members],
            20,
            f"Users with {role}"
        )

    @commands.command(
        brief="Shows people with all of the listed roles"
    )
    async def hasroles(self, ctx: aoi.AoiContext, roles: commands.Greedy[discord.Role]):
        users: List[discord.Member] = []
        for user in ctx.guild.members:
            role_ids = [role.id for role in user.roles]
            if all(role.id in role_ids for role in roles):
                users.append(user)
        await ctx.paginate(
            [f"{user.mention} - {user.id} - {user}" for user in users],
            20,
            f"Users with: {', '.join(map(str, roles))}"
        )

    @commands.command(
        brief="Shows the number of members with each role",
        flags={"stacked": [None, "Only count the highest of the roles if someone has multiple. "
                                 "Respect discord role order"],
               "sort": [None, "Sort roles by member count"]},
        aliases=["rcompare"]
    )
    async def rolecompare(self, ctx: aoi.AoiContext, roles: commands.Greedy[discord.Role]):
        if len(roles) < 2 or len(roles) > 20:
            raise commands.BadArgument("You must supply 2-20 roles.")
        if "stacked" not in ctx.flags:
            return await ctx.embed(description="\n".join(
                (f"{n + 1}. {role} - {len(role.members)}"
                 for n, role in enumerate(sorted(roles, key=lambda x: -len(x.members))))
                if "sort" in ctx.flags else
                (f"{role} - {len(role.members)}" for role in roles)
            ))
        members: Dict[discord.Member, discord.Role] = {}
        await ctx.trigger_typing()
        for member in ctx.guild.members:
            role_ids: List[int] = [r.id for r in member.roles]
            # grab member's highest role in the list
            for role in roles:
                if role.id in role_ids:
                    if member not in members:
                        members[member] = role
                    elif role.position > members[member].position:
                        members[member] = role

        count: Dict[discord.Role, int] = {
            role: m.count(members.values(), lambda x: x.id == role.id)
            for role in roles
        }
        if "sort" in ctx.flags:
            count = dict(sorted(count.items(), key=lambda i: -i[1]))  # noqa what the fuck pycharm

        await ctx.embed(
            description="\n".join(
                (f"{n + 1}. {i[0]} - {i[1]}" for n, i in enumerate(count.items()))  # noqa also what the fuck pycharm
                if "sort" in ctx.flags else
                (f"{role} - {members}" for role, members in count.items())
            )
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Information(bot))
