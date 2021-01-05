from datetime import datetime
from typing import List, Union

import aoi
import discord
from aoi.database import Punishment, PunishmentType
from discord.ext import commands


def _soft_check_role(ctx: aoi.AoiContext, member: discord.Member, action: str = "edit"):
    if member.top_role >= ctx.me.top_role:
        raise aoi.RoleHierarchyError(f"I can't {action} someone with a role higher than mine")


class Moderation(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    def _check_role(self, ctx: aoi.AoiContext, member: discord.Member, action: str = "edit"):
        if member.top_role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleHierarchyError(f"You can't {action} someone with a role higher than yours")
        if member.top_role >= ctx.me.top_role:
            raise aoi.RoleHierarchyError(f"I can't {action} someone with a role higher than mine")
        if member.id == ctx.guild.owner_id:
            raise aoi.RoleHierarchyError(f"We can't {action} the server owner")

    def get_action_embed(self, ctx: aoi.AoiContext, member: Union[discord.Member, discord.User],
                         typ: int, reason: str = None, extra: str = None) -> discord.Embed:
        action = ["banned", "kicked", "muted", "warned", "unbanned", "soft-banned"][typ]
        return discord.Embed(title=f"User {action}", timestamp=datetime.now(), description=f"{reason}\n\n{extra}"). \
            add_field(name="User", value=str(member)). \
            add_field(name="ID", value=str(member.id)). \
            add_field(name="Staff Member", value=ctx.author.mention). \
            set_thumbnail(url=member.avatar_url)

    @property
    def description(self) -> str:
        return "Commands for moderation"

    @commands.bot_has_permissions(kick_members=True)
    @commands.has_permissions(kick_members=True)
    @commands.command(brief="Kicks a member from the server")
    async def kick(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = None):
        self._check_role(ctx, member, "kick")
        await member.kick(reason=f"{reason} | {ctx.author.id} {ctx.author}")
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.KICK, reason))
        await self.bot.db.add_user_kick(member.id, ctx, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Bans a member from the server")
    async def ban(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = None):
        self._check_role(ctx, member, "ban")
        await member.ban(reason=f"{reason} | {ctx.author.id} {ctx.author}")
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.BAN, reason))
        await self.bot.db.add_user_ban(member.id, ctx, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Softbans a member from the server")
    async def softban(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = None):
        self._check_role(ctx, member, "softban")
        await member.ban(reason=f"{reason} | {ctx.author.id} {ctx.author} | Softban")
        await ctx.guild.unban(member, reason=f"Softban")
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.SOFTBAN, reason))
        await self.bot.db.add_punishment(member.id, ctx.guild.id, ctx.author.id, PunishmentType.SOFTBAN, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Unbans a member from the server")
    async def unban(self, ctx: aoi.AoiContext, user: Union[discord.User, int], *, reason: str = None):
        if isinstance(user, discord.User):
            user = user.id
        entries: List[discord.guild.BanEntry] = await ctx.guild.bans()
        found: discord.guild.BanEntry
        for ban in entries:
            if ban.user.id == user:
                found = ban
                break
        else:
            return await ctx.send_error(f"User ID {user} not banned from this server")
        user = await self.bot.fetch_unknown_user(user)
        await ctx.guild.unban(found.user, reason=f"{reason} | {ctx.author.id} {ctx.author}")
        await ctx.send(embed=self.get_action_embed(ctx, user, PunishmentType.UNBAN, reason))
        await self.bot.db.add_punishment(user.id, ctx.guild.id, ctx.author.id, PunishmentType.UNBAN, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Bans a member from the server")
    async def warn(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = "No reason provided"):
        self._check_role(ctx, member, "warn")
        dm_sent = True
        try:
            await member.send(embed=discord.Embed(title=f"Warning from {ctx.guild}", description=reason))
        except discord.Forbidden:
            dm_sent = False
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.WARN, reason,
                                                   extra="DM could not be sent" if not dm_sent else ""))
        await self.bot.db.add_user_warn(member.id, ctx, reason)

    @commands.command(brief="Views the punishment logs for a user")
    async def logs(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        if member.id != ctx.author.id and not ctx.author.permissions_in(ctx.channel).kick_members:
            return await ctx.send_error("You need the kick members permission to see logs from other people")
        punishments: List[Punishment] = sorted(await self.bot.db.lookup_punishments(member.id),
                                               key=lambda punishment: punishment.time, reverse=True)

        async def fmt(punishment: Punishment) -> str:
            action = ["banned", "kicked", "muted", "warned", "unbanned", "softbanned"][punishment.typ]
            return f"{action} by {await self.bot.fetch_unknown_user(punishment.staff)}\n" \
                   f"Date: {punishment.time.strftime('%x %X')}\n" \
                   f"Reason: {punishment.reason or 'None'}\n"

        await ctx.paginate([await fmt(punishment) for punishment in punishments],
                           10, f"Punishments for {member}", numbered=True, num_start=1)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Moderation(bot))
