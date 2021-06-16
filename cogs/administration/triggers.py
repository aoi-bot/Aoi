from typing import Dict, List, Optional

from aiosqlite import Connection

import aoi
import discord
from aoi.triggers import Trigger
from discord.ext import commands
from discord.ext.commands import RoleConverter


# TODO help refactor

class Triggers(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.role_add_triggers: Dict[int, Dict[int, Trigger]] = {}
        self.role_remove_triggers: Dict[int, Dict[int, Trigger]] = {}
        self.db: Optional[Connection] = None
        bot.loop.create_task(self.dbload())

    @property
    def description(self) -> str:
        return f"Add custom triggers to {self.bot.user.name if self.bot.user else ''}"

    async def dbload(self):
        await self.bot.wait_until_ready()
        self.db = self.bot.db.conn
        rows = await self.db.execute_fetchall("SELECT * FROM roletriggers")

        for row in rows:
            guild = row[0]
            role = row[1]
            channel = row[2]
            message = row[3]
            typ = row[4]

            if typ == "add":
                await self._append_roleadd_trigger(guild, role, channel, message, False)
            else:
                await self._append_roleremove_trigger(guild, role, channel, message, False)

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Set a trigger for a role addition", aliases=["onra"])
    async def onroleadd(self, ctx: aoi.AoiContext, role: discord.Role, channel: discord.TextChannel, *, message: str):
        await self._append_roleadd_trigger(ctx.guild.id, role.id, channel.id, message, True)
        await ctx.send_ok(f"Message will be sent in {channel.mention} when {role.mention} is added.")

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Set a trigger for a role removal", aliases=["onrr"])
    async def onroleremove(self, ctx: aoi.AoiContext, role: discord.Role, channel: discord.TextChannel, *,
                           message: str):
        await self._append_roleremove_trigger(ctx.guild.id, role.id, channel.id, message, True)
        await ctx.send_ok(f"Message will be sent in {channel.mention} when {role.mention} is removed.")

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Remove a trigger", aliases=["remtr"])
    async def removetrigger(self, ctx: aoi.AoiContext, trigger_type: str, *, arg: str):
        supported_trigger_types = ["addrole", "removerole"]
        if trigger_type not in supported_trigger_types:
            return await ctx.send_error(f"{trigger_type} not a supported trigger type. It must be one of: " +
                                        " ".join(f"`{typ}`" for typ in supported_trigger_types))
        if trigger_type in ["addrole", "removerole"]:
            role: discord.Role = await RoleConverter().convert(ctx, arg)
            if trigger_type == "addrole":
                if ctx.guild.id not in self.role_add_triggers or role.id not in self.role_add_triggers[ctx.guild.id]:
                    return await ctx.send_error(f"There isn't an addrole trigger for {role.mention}")
                await self._remove_roleadd_trigger(ctx.guild.id, role.id)
            else:
                if ctx.guild.id not in self.role_remove_triggers or role.id not in self.role_remove_triggers[
                        ctx.guild.id]:
                    return await ctx.send_error(f"There isn't an removerole trigger for {role.mention}")
                await self._remove_roleremove_trigger(ctx.guild.id, role.id)
            await ctx.send_ok(f"Trigger for {role.mention} removed.")

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Lists the role triggers", aliases=["roletr", "roletrigger"])
    async def roletriggers(self, ctx: aoi.AoiContext, for_role: discord.Role = None,  # noqa C901
                           add_or_remove: str = None):  # noqa C901
        rows = await self.db.execute_fetchall("SELECT * FROM roletriggers WHERE guild=?", (ctx.guild.id,))
        valid_rows = []
        lost_rows = []

        adds = {}
        removes = {}
        union = []

        # find and remove triggers for deleted roles
        for row in rows:
            if ctx.guild.get_role(row[1]):
                valid_rows.append(row)
            else:
                lost_rows.append(row)
        for row in lost_rows:
            if row[4] == "add":
                await self._remove_roleadd_trigger(ctx.guild.id, row[1])
            else:
                await self._remove_roleremove_trigger(ctx.guild.id, row[1])

        if not for_role:
            for row in valid_rows:
                role = row[1]
                channel = row[2]
                typ = row[4]
                if typ == "add":
                    adds[role] = channel
                else:
                    removes[role] = channel
                if role not in union:
                    union.append(role)

            def fmt(r: int):
                add = f"Message sent in <#{adds[r]}> when added\n" if r in adds else ""
                remove = f"Message sent in <#{removes[r]}> when removed\n" if r in removes else ""
                return f"<@&{r}>\n{add}{remove}"

            return await ctx.paginate([fmt(r) for r in union], 10, f"Role Triggers for {ctx.guild}")
        if not add_or_remove or add_or_remove not in ["add", "remove"]:
            return await ctx.send_error("`add` or `remove` must be supplied when looking up a role trigger message")
        row = await (await self.db.execute("SELECT * FROM roletriggers WHERE guild=? AND type=? AND role=?",
                                           (ctx.guild.id, add_or_remove, for_role.id))).fetchone()
        if not row:
            return await ctx.send_error(f"No trigger found for {for_role.mention} {add_or_remove}")
        await ctx.embed(description=f"Send in <#{row[2]}> on {for_role.mention} {add_or_remove}\n\n"
                                    f"```{row[3][:1800]}```")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        remove_set: List[discord.Role] = list(set(before.roles) - set(after.roles))
        add_set: List[discord.Role] = list(set(after.roles) - set(before.roles))
        if remove_set:
            if before.guild.id not in self.role_remove_triggers:
                return
            if remove_set[0].id in self.role_remove_triggers[before.guild.id]:
                await self.role_remove_triggers[before.guild.id][remove_set[0].id].run(before)
        if add_set:
            if before.guild.id not in self.role_add_triggers:
                return
            if add_set[0].id in self.role_add_triggers[before.guild.id]:
                await self.role_add_triggers[before.guild.id][add_set[0].id].run(before)

    async def _append_roleadd_trigger(self, guild: int, role: int, channel: int, message: str, write: bool = False):
        async def send_coro(member: discord.Member):
            await self.bot.send_json_to_channel(
                self.bot.get_guild(guild).get_channel(channel).id,  # paranoia go brrr
                message,
                member=member
            )

        if guild not in self.role_add_triggers:
            self.role_add_triggers[guild] = {}
        self.role_add_triggers[guild][role] = Trigger(send_coro)

        if write:
            await self.db.execute("DELETE FROM roletriggers WHERE guild=? AND type=? AND role=?", (guild, "add", role))
            await self.db.execute("INSERT INTO roletriggers VALUES (?,?,?,?,?)",
                                  (guild, role, channel, message, "add"))
            await self.db.commit()

    async def _append_roleremove_trigger(self, guild: int, role: int, channel: int, message: str, write: bool = False):
        async def send_coro(member: discord.Member):
            await self.bot.send_json_to_channel(
                self.bot.get_guild(guild).get_channel(channel).id,  # paranoia go brrr
                message,
                member=member
            )

        if guild not in self.role_remove_triggers:
            self.role_remove_triggers[guild] = {}
        self.role_remove_triggers[guild][role] = Trigger(send_coro)

        if write:
            await self.db.execute("DELETE FROM roletriggers WHERE guild=? AND type=? AND role=?",
                                  (guild, "remove", role))
            await self.db.execute("INSERT INTO roletriggers VALUES (?,?,?,?,?)",
                                  (guild, role, channel, message, "remove"))
            await self.db.commit()

    async def _remove_roleadd_trigger(self, guild: int, role: int):
        del self.role_add_triggers[guild][role]
        await self.db.execute("DELETE FROM roletriggers WHERE guild=? AND type=? AND role=?", (guild, "add", role))
        await self.db.commit()

    async def _remove_roleremove_trigger(self, guild: int, role: int):
        del self.role_remove_triggers[guild][role]
        await self.db.execute("DELETE FROM roletriggers WHERE guild=? AND type=? AND role=?", (guild, "remove", role))
        await self.db.commit()


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Triggers(bot))
