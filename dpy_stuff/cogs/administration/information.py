from typing import Dict, List, Optional, Union

import discord
from discord.ext import commands

from aoi import bot
from aoi.libs import misc as m, conversions


class Information(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @commands.command(brief="Shows info on a text channel", aliases=["tcinfo"])
    async def textinfo(self, ctx: bot.AoiContext, *, channel: discord.TextChannel):
        await ctx.embed(
            title=f"Info for {channel}",
            fields=[
                ("ID", channel.id),
                ("Created at", channel.created_at.strftime("%c")),
                (
                    "Slowmode",
                    f"{channel.slowmode_delay}s" if channel.slowmode_delay else "No Slowmode",
                ),
            ],
        )

    @commands.command(brief="Shows the server's emojis")
    async def emojis(self, ctx: bot.AoiContext):
        if not ctx.guild.emojis:
            return await ctx.send_info("Server has no emojis")
        await ctx.paginate(
            lst=[f"{str(e)} | {e.name} | {e.id}" for e in ctx.guild.emojis],
            n=20,
            title=f"{ctx.guild}'s emojis",
            numbered=False,
        )

    @commands.command(
        brief="Shows your or a member's permissions in a channel. Defaults to the current channel.",
        aliases=["perms"],
    )
    async def permissions(
        self,
        ctx: bot.AoiContext,
        member: Optional[discord.Member] = None,
        channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]] = None,
    ):
        channel = channel or ctx.channel
        member = member or ctx.author
        perms = channel.permissions_for(member)
        await ctx.embed(
            title=f"Permissions for {member} in {channel}",
            thumbnail=member.avatar.url,
            description="```diff\n"
            + "\n".join(
                f"{'+' if perm[1] or perms.administrator else '-'} " f"{conversions.camel_to_title(perm[0])}"
                for perm in perms
            )
            + "```",
        )

    @commands.command(
        brief="Shows a role's permissions, optionally in a channel. Defaults to showing the role's server-wide "
        "permissions",
        aliases=["rperms", "roleperms"],
    )
    async def rolepermissions(
        self,
        ctx: bot.AoiContext,
        role: Union[discord.Role, str],
        channel: Optional[Union[discord.TextChannel, discord.VoiceChannel]] = None,
    ):
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
                description="```diff\n"
                + "\n".join(
                    f"{'+' if perm[1] or perms.administrator else '-'} " f"{conversions.camel_to_title(perm[0])}"
                    for perm in perms
                )
                + "```",
            )
        overwrite: discord.PermissionOverwrite = channel.overwrites_for(role)
        if not overwrite:
            return await ctx.send_info(f"No permission overwrites in {channel} for {role}")
        return await ctx.embed(
            title=f"Permission overwrite for {role} in {channel}",
            description="```diff\n"
            + "\n".join(f"{_(perm, overwrite)} " f"{conversions.camel_to_title(perm[0])}" for perm in overwrite)
            + "```",
        )

    @commands.command(brief="Shows people in a role")
    async def hasrole(self, ctx: bot.AoiContext, *, role: discord.Role):
        await ctx.paginate(
            [f"{user.mention} - {user.id} - {user}" for user in role.members],
            20,
            f"Users with {role}",
        )

    @commands.command(brief="Shows people with all of the listed roles")
    async def hasroles(self, ctx: bot.AoiContext, roles: commands.Greedy[discord.Role]):
        users: List[discord.Member] = []
        for user in ctx.guild.members:
            role_ids = [role.id for role in user.roles]
            if all(role.id in role_ids for role in roles):
                users.append(user)
        await ctx.paginate(
            [f"{user.mention} - {user.id} - {user}" for user in users],
            20,
            f"Users with: {', '.join(map(str, roles))}",
        )

    @commands.command(
        brief="Shows the number of members with each role",
        flags={
            "stacked": [
                None,
                "Only count the highest of the roles if someone has multiple. " "Respect discord role order",
            ],
            "sort": [None, "Sort roles by member count"],
        },
        aliases=["rcompare"],
    )
    async def rolecompare(self, ctx: bot.AoiContext, roles: commands.Greedy[discord.Role]):
        if len(roles) < 2 or len(roles) > 20:
            raise commands.BadArgument("You must supply 2-20 roles.")
        if "stacked" not in ctx.flags:
            return await ctx.embed(
                description="\n".join(
                    (
                        f"{n + 1}. {role} - {len(role.members)}"
                        for n, role in enumerate(sorted(roles, key=lambda x: -len(x.members)))
                    )
                    if "sort" in ctx.flags
                    else (f"{role} - {len(role.members)}" for role in roles)
                )
            )
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

        count: Dict[discord.Role, int] = {role: m.count(members.values(), lambda x: x.id == role.id) for role in roles}
        if "sort" in ctx.flags:
            count = dict(sorted(count.items(), key=lambda i: -i[1]))  # noqa what the fuck pycharm

        await ctx.embed(
            description="\n".join(
                (f"{n + 1}. {i[0]} - {i[1]}" for n, i in enumerate(count.items()))  # noqa also what the fuck pycharm
                if "sort" in ctx.flags
                else (f"{role} - {members}" for role, members in count.items())
            )
        )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(Information(bot))
