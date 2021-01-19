import asyncio
from datetime import datetime
from typing import List, Union, Optional, Dict

import aoi
import discord
from aoi.database import Punishment, PunishmentType, TimedPunishment
from discord.ext import commands


def _soft_check_role(ctx: aoi.AoiContext, member: discord.Member, action: str = "edit"):
    if member.top_role >= ctx.me.top_role:
        raise aoi.RoleHierarchyError(f"I can't {action} someone with a role higher than mine")


class Moderation(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.timed_punishments: Dict[int, List[TimedPunishment]] = {}
        bot.loop.create_task(self._init())

    async def _init(self):
        await self.bot.wait_until_ready()
        self.timed_punishments = await self.bot.db.load_backing_punishments()

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
        dm_sent = await self._dm(member, discord.Embed(title=f"Kicked from {ctx.guild}", description=reason))
        await member.kick(reason=f"{reason} | {ctx.author.id} {ctx.author}")
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.KICK, reason,
                                                   extra="DM could not be sent" if not dm_sent else ""))
        await self.bot.db.add_user_kick(member.id, ctx, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Bans a member from the server")
    async def ban(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = None):
        self._check_role(ctx, member, "ban")
        dm_sent = await self._dm(member, discord.Embed(title=f"Banned from {ctx.guild}", description=reason))
        await member.ban(reason=f"{reason} | {ctx.author.id} {ctx.author}")
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.BAN, reason,
                                                   extra="DM could not be sent" if not dm_sent else ""))
        await self.bot.db.add_user_ban(member.id, ctx, reason)

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Softbans a member from the server")
    async def softban(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = None):
        self._check_role(ctx, member, "softban")
        dm_sent = await self._dm(member, discord.Embed(title=f"Softbanned from {ctx.guild}", description=reason))
        await member.ban(reason=f"{reason} | {ctx.author.id} {ctx.author} | Softban")
        await ctx.guild.unban(member, reason=f"Softban")
        await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.SOFTBAN, reason,
                                                   extra="DM could not be sent" if not dm_sent else ""))
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

    @commands.has_permissions(kick_members=True)
    @commands.command(brief="Warns a member")
    async def warn(self, ctx: aoi.AoiContext, member: discord.Member, *, reason: str = "No reason provided"):
        self._check_role(ctx, member, "warn")
        dm_sent = await self._dm(member, discord.Embed(title=f"Warning from {ctx.guild}", description=reason))
        msg = await ctx.send(embed=self.get_action_embed(ctx, member, PunishmentType.WARN, reason,
                                                         extra="DM could not be sent" if not dm_sent else ""))
        await self.bot.db.add_user_warn(member.id, ctx, reason)

        punishments = [x for x in (await self.bot.db.lookup_punishments(member.id)) if x.typ == PunishmentType.WARN]
        punishment = await self.bot.db.get_warnp(ctx.guild.id, len(punishments))

        await asyncio.sleep(0.01)  # make sure timestamps differ enough

        if punishment == "kick":
            await self._dm(member, discord.Embed(title=f"Kicked from {ctx.guild}", description="Automod"))
            await member.kick(reason="Automod")
            await self.bot.db.add_user_kick(member.id, ctx, "Automod")
            await msg.edit(embed=msg.embeds[0].add_field(name="Automod Kicked", value=f"{len(punishments)} warns"))
        elif punishment == "ban":
            await self._dm(member, discord.Embed(title=f"Banned from {ctx.guild}", description="Automod"))
            await member.ban(reason="Automod")
            await self.bot.db.add_user_ban(member.id, ctx, "Automod")
            await msg.edit(embed=msg.embeds[0].add_field(name="Automod Banned", value=f"{len(punishments)} warns"))

    @commands.has_permissions(ban_members=True)
    @commands.command(brief="Clears a warning for a user", aliases=["pclear"])
    async def punishmentclear(self, ctx: aoi.AoiContext, member: discord.Member, num: int = 1):
        punishments: List[Punishment] = sorted(await self.bot.db.lookup_punishments(member.id),
                                               key=lambda punishment: punishment.time, reverse=True)
        if num < 1 or num > len(punishments):
            return ctx.send_error("Invalid warning number")
        await self.bot.db.db.execute("delete from punishments where user=? and guild=? and timestamp=?",
                                     (punishments[num-1].user,
                                      punishments[num-1].guild,
                                      punishments[num-1].time.timestamp()))
        await self.bot.db.db.commit()
        await ctx.send_ok(f"Cleared punishment #{num} for {member}")

    @commands.command(brief="Views the punishment logs for a user")
    async def logs(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        if member.id != ctx.author.id and not ctx.author.permissions_in(ctx.channel).kick_members:
            return await ctx.send_error("You need the kick members permission to see logs from other people")
        punishments: List[Punishment] = sorted(await self.bot.db.lookup_punishments(member.id),
                                               key=lambda punishment: punishment.time, reverse=True)

        if not punishments:
            await ctx.send_info(f"{member} has no punishments")

        async def fmt(punishment: Punishment) -> str:
            action = ["banned", "kicked", "muted", "warned", "unbanned", "softbanned"][punishment.typ]
            return f"{action} by {await self.bot.fetch_unknown_user(punishment.staff)}\n" \
                   f"Date: {punishment.time.strftime('%x %X')}\n" \
                   f"Reason: {punishment.reason or 'None'}\n"

        await ctx.paginate([await fmt(punishment) for punishment in punishments],
                           10, f"Punishments for {member}", numbered=True, num_start=1)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Adds or removes a warn punishment")
    async def warnp(self, ctx: aoi.AoiContext, warns: int, *, action: str = None):
        if not action:
            await self.bot.db.del_warnp(ctx.guild.id, warns)
            return await ctx.send(f"No punishment will be applied at {warns} warns")
        res = await self._validate_warnp(action)
        if res:
            return ctx.send_error(res)
        await self.bot.db.set_warnp(ctx.guild.id, warns, action)
        return await ctx.send_ok(f"`{action}` will be applied at {warns} warns")

    @commands.command(brief="View the server's warning punishment list")
    async def warnpl(self, ctx: aoi.AoiContext):
        punishments = await self.bot.db.get_all_warnp(ctx.guild.id)
        if punishments:
            await ctx.paginate([f"{n}: {p}" for n, p in punishments], title="Warn Punishments", n=20)
        else:
            await ctx.send_info("No warning punishments for this server")

    async def _validate_warnp(self, warnp: str) -> Optional[str]:
        args = warnp.lower().split()
        if args[0] == "kick":
            return None if len(args) == 1 else "Kick takes no extra arguments"
        if args[0] == "ban":
            return None if len(args) == 1 else "Ban takes no extra arguments"
        return "Must give either kick or ban"

    async def _dm(self, member: discord.Member, embed: discord.Embed):
        try:
            await member.send(embed=embed)
            return True
        except discord.Forbidden:
            return True


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Moderation(bot))
