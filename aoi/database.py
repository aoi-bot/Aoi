from __future__ import annotations

import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Dict, Optional, List, TYPE_CHECKING, Union, Tuple

import aiosqlite
import discord
from aiosqlite import Connection
from discord.ext import tasks, commands

if TYPE_CHECKING:
    import aoi


@dataclass
class _GuildSetting:
    ok_color: int
    error_color: int
    info_color: int
    perm_errors: bool


@dataclass(frozen=True)
class _Punishment:
    user: int
    guild: int
    staff: int
    typ: int
    reason: str
    time: datetime.datetime


class PunishmentType:
    BAN = 0
    KICK = 1
    MUTE = 2
    WARN = 3


class AoiDatabase:
    def __init__(self, bot: aoi.AoiBot):
        self.db: Optional[Connection] = None
        self.bot = bot

        self.guild_settings: Dict[int, _GuildSetting] = {}
        self.prefixes: Dict[int, str] = {}
        self.perm_chains: Dict[int, List[str]] = {}

        self.xp_lock = asyncio.Lock()
        self.title_lock = asyncio.Lock()
        self.global_currency_lock = asyncio.Lock()
        self.guild_currency_lock = asyncio.Lock()
        self.currency_gain_lock = asyncio.Lock()

        self.xp: Dict[int, Dict[int, int]] = {}
        self.changed_xp: Dict[int, List[int]] = {}
        self.global_currency: Dict[int, int] = {}
        self.changed_global_currency: List[int] = []
        self.global_xp: Dict[int, int] = {}
        self.guild_currency: Dict[int, Dict[int, int]] = {}
        self.changed_guild_currency: Dict[int, List[int]] = {}
        self.currency_gains: Dict[int, int] = {}
        self.changed_currency_gains: List[int] = []

        self.titles: Dict[int, str] = {}
        self.owned_titles: Dict[int, List[str]] = {}
        self.badges: Dict[int, List[str]] = {}
        self.owned_badges: Dict[int, List[str]] = {}
        self.backgrounds: Dict[int, str] = {}
        self.changed_global_users: List[int] = []

        self.xp_cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 180.0, commands.BucketType.member)
        self.global_currency_cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 60.0, commands.BucketType.user)

    async def ensure_currency_gain(self, guild: discord.Guild):
        if guild.id not in self.currency_gains:
            async with self.currency_gain_lock:
                if guild.id not in self.changed_currency_gains:
                    self.changed_currency_gains.append(guild.id)
                self.currency_gains[guild.id] = 0

    async def set_currency_gain(self, guild: discord.Guild, new: int):
        await self.ensure_currency_gain(guild)
        async with self.currency_gain_lock:
            if guild.id not in self.changed_currency_gains:
                self.changed_currency_gains.append(guild.id)
            self.currency_gains[guild.id] = new

    async def get_currency_gain(self, guild: discord.Guild):
        await self.ensure_currency_gain(guild)
        return self.currency_gains[guild.id]

    async def ensure_user_entry(self, member: discord.Member):
        async with self.title_lock:
            if member.id not in self.titles:
                self.titles[member.id] = ""
            if member.id not in self.owned_titles:
                self.owned_titles[member.id] = []
            if member.id not in self.badges:
                self.badges[member.id] = []
            if member.id not in self.owned_badges:
                self.owned_badges[member.id] = []
            if member.id not in self.backgrounds:
                self.backgrounds[member.id] = ""
            if member.id not in self.changed_global_users:
                self.changed_global_users.append(member.id)

    async def get_titles(self, member: discord.Member) -> Tuple[str, List[str]]:
        await self.ensure_user_entry(member)
        return self.titles[member.id], self.owned_titles[member.id]

    async def get_badges(self, member: discord.Member) -> Tuple[List[str], List[str]]:
        await self.ensure_user_entry(member)
        return self.badges[member.id], self.owned_badges[member.id]

    async def add_title(self, member: discord.Member, title: str):
        await self.ensure_user_entry(member)
        async with self.title_lock:
            self.owned_titles[member.id].append(title)
        await self.cache_flush()

    async def equip_title(self, member: discord.Member, index: int):
        await self.ensure_user_entry(member)
        async with self.title_lock:
            self.titles[member.id] = self.owned_titles[member.id][index]
        await self.cache_flush()

    async def load(self):
        logging.info("database:Connecting to database")
        self.db = await aiosqlite.connect("database.db")
        logging.info("database:Loading database into memory")
        cursor = await self.db.execute("SELECT * from guild_settings")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.guild_settings[r[0]] = _GuildSetting(*(int(color, 16) for color in r[1:4]),
                                                      r[5])
            self.prefixes[r[0]] = r[4]
        cursor = await self.db.execute("SELECT * from permissions")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.perm_chains[r[0]] = r[1].split(";")
        logging.info("database:Database loaded")

        # load guilds that dont exist in the database
        for i in self.bot.guilds:
            await self.guild_setting(i.id)
            await self.get_permissions(i.id)

        cursor = await self.db.execute("SELECT * from xp")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            if r[1] not in self.xp:
                self.xp[r[1]] = {}
            self.xp[r[1]][r[0]] = r[2]
            self.global_xp[r[0]] = self.global_xp.get(r[0], 0) + r[2]

        # load global currency
        cursor = await self.db.execute("SELECT * from global_currency")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.global_currency[r[0]] = r[1]

        cursor = await self.db.execute("SELECT * from user_global")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.titles[r[0]] = r[1]
            self.badges[r[0]] = r[2].split(",")
            self.owned_titles[r[0]] = r[3].split(",")
            self.owned_badges[r[0]] = r[4].split(",")
            self.backgrounds[r[0]] = r[5]

        cursor = await self.db.execute("select * from currency_gains")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.currency_gains[r[0]] = r[1]

        for i in self.bot.guilds:
            await self.ensure_currency_gain(i)

        cursor = await self.db.execute("select * from guild_currency")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            if r[0] not in self.guild_currency:
                self.guild_currency[r[0]] = {}
            self.guild_currency[r[0]][r[1]] = r[2]

        for i in self.bot.guilds:
            for m in i.members:
                await self.ensure_user_entry(m)

        self._cache_flush_loop.start()

    async def close(self):
        await self.cache_flush()
        await self.db.close()

    async def ensure_guild_currency_entry(self, member: discord.Member):
        logging.log(15, "guild_cur:ensure:waiting for lock")
        async with self.guild_currency_lock:
            logging.log(15, "guild_cur:ensure:-got lock")
            if member.guild.id not in self.guild_currency:
                self.guild_currency[member.guild.id] = {}
            if member.id not in self.guild_currency[member.guild.id]:
                self.guild_currency[member.guild.id][member.id] = 0
            if member.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[member.guild.id] = []
            if member.id not in self.changed_guild_currency[member.guild.id]:
                self.changed_guild_currency[member.guild.id].append(member.id)
        logging.log(15, f"guild_cur:ensure:-releasing lock")

    async def get_guild_currency(self, member: discord.Member) -> int:
        await self.ensure_guild_currency_entry(member)
        return self.guild_currency[member.guild.id][member.id]

    async def award_guild_currency(self, member: discord.Member, amount: int):
        await self.ensure_guild_currency_entry(member)
        async with self.guild_currency_lock:
            self.guild_currency[member.guild.id][member.id] += amount
            if member.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[member.guild.id] = []
            if member.id not in self.changed_guild_currency[member.guild.id]:
                self.changed_guild_currency[member.guild.id].append(member.id)

    async def get_global_currency(self, member: discord.Member):
        await self.ensure_global_currency_entry(member)
        return self.global_currency[member.id]

    async def award_global_currency(self, member: discord.Member, amount: int):
        async with self.global_currency_lock:
            self.global_currency[member.id] = self.global_currency.get(member.id, 0) + amount
            if member.id not in self.changed_global_currency:
                self.changed_global_currency.append(member.id)

    async def get_badges_titles(self, member: discord.Member) -> Tuple[str, List[str], List[str], List[str], str]:
        await self.ensure_user_entry(member)
        async with self.title_lock:
            if member.id not in self.titles:
                self.titles[member.id] = ""
                self.badges[member.id] = []
                self.owned_badges[member.id] = []
                self.owned_titles[member.id] = []
                await self.db.execute("insert into user_global (user, title, badges, owned_titles, owned_badges) "
                                      "values (?,?,?,?,?)", (member.id, "", "", "", ""))
                await self.db.commit()
            return self.titles[member.id], self.badges[member.id], self.owned_titles[member.id], \
                   self.owned_badges[member.id], self.backgrounds[member.id]

    async def ensure_xp_entry(self, msg: Union[discord.Message, discord.Member]):
        if isinstance(msg, discord.Message):
            guild_id = msg.guild.id
            user_id = msg.author.id
        else:
            guild_id = msg.guild.id
            user_id = msg.id
        logging.log(15, "xp:ensure:waiting for lock")
        async with self.xp_lock:
            logging.log(15, "xp:ensure:-got lock")
            if user_id not in self.global_xp:
                self.global_xp[user_id] = 0
                for _, v in self.xp.items():
                    self.global_xp[user_id] += v.get(user_id, 0)
            if guild_id not in self.xp:
                self.xp[guild_id] = {}
            if user_id not in self.xp[guild_id]:
                self.xp[guild_id][user_id] = 0
            if guild_id not in self.changed_xp:
                self.changed_xp[guild_id] = []
            if user_id not in self.changed_xp[guild_id]:
                self.changed_xp[guild_id].append(user_id)
        logging.log(15, f"xp:ensure:-releasing lock")

    async def ensure_global_currency_entry(self, member: discord.Member):
        async with self.global_currency_lock:
            if member.id not in self.global_currency:
                self.global_currency[member.id] = 0
                if member.id not in self.changed_global_currency:
                    self.changed_global_currency.append(member.id)

    async def add_xp(self, msg: discord.Message):
        if msg.author.bot:
            return
        if self.xp_cooldown.get_bucket(msg).update_rate_limit():
            return
        logging.log(15, f"xp:add:ensure xp entry for {msg.author}")
        await self.ensure_xp_entry(msg)
        c = 0
        for i in msg.guild.members:
            if not i.bot:
                c += 1
            if c == 3:
                break
        if c < 3:
            return
        logging.log(15, f"xp:add:waiting for lock")
        async with self.xp_lock:
            logging.log(15, f"xp:add:-got lock")
            self.xp[msg.guild.id][msg.author.id] += 3
            self.global_xp[msg.author.id] += 3
            if msg.author.id not in self.changed_xp[msg.guild.id]:
                logging.log(15, f"xp:add:-adding user change for {msg.author}")
                self.changed_xp[msg.guild.id].append(msg.author.id)
        logging.log(15, f"xp:add:-releasing lock")
        await self.ensure_currency_gain(msg.guild)
        await self.ensure_guild_currency_entry(msg.author)
        async with self.guild_currency_lock:
            self.guild_currency[msg.guild.id][msg.author.id] += self.currency_gains[msg.guild.id]
            if msg.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[msg.guild.id] = []
            if msg.author.id not in self.changed_guild_currency[msg.guild.id]:
                self.changed_guild_currency[msg.guild.id].append(msg.author.id)

    async def add_global_currency(self, msg: discord.Message):
        if self.global_currency_cooldown.get_bucket(msg).update_rate_limit():
            return
        async with self.global_currency_lock:
            self.global_currency[msg.author.id] = self.global_currency.get(msg.author.id, 0) + 1
            if msg.author.id not in self.changed_global_currency:
                self.changed_global_currency.append(msg.author.id)

    @tasks.loop(minutes=1)
    async def _cache_flush_loop(self):
        await self.cache_flush()

    async def cache_flush(self):
        logging.log(15, "xp:flush:waiting for lock")
        async with self.xp_lock:
            logging.log(15, "xp:flush:-got lock")
            for guild, users in self.changed_xp.items():
                for u in users:
                    xp = self.xp[guild][u]
                    logging.log(15, f"xp:flush:-checking user {self.bot.get_user(u)}")
                    a = await self.db.execute("SELECT * from xp where guild = ? and user=?", (guild, u))
                    if not await a.fetchall():
                        logging.log(15, f"xp:flush:-adding user {self.bot.get_user(u)}")
                        await self.db.execute("INSERT INTO xp (user, guild, xp) values (?,?,?)", (u, guild, 0))
                    logging.log(15, f"xp:flush:-updating user {self.bot.get_user(u)}")
                    await self.db.execute("UPDATE xp set xp=? where user=? and guild=?", (xp, u, guild))
            await self.db.commit()
            self.changed_xp = {}
        logging.log(15, "xp:flush:released")
        async with self.global_currency_lock:
            for u in self.changed_global_currency:
                a = await self.db.execute("SELECT * from global_currency where user=?",
                                          (u,))
                if not await a.fetchall():
                    await self.db.execute("insert into global_currency (user, amount) "
                                          "values (?,?)", (u, 0))
                await self.db.execute("update global_currency set amount=? where user=?",
                                      (self.global_currency[u], u))
            await self.db.commit()
            self.changed_global_currency = []
        async with self.title_lock:
            for u in self.changed_global_users:
                a = await self.db.execute("select * from user_global where user=?", (u,))
                if not await a.fetchall():
                    await self.db.execute("insert into user_global (user, title, badges, owned_titles, owned_badges,"
                                          "background) "
                                          "values (?,?,?,?,?,?)", (u, "", "", "", "", ""))
                await self.db.execute("update user_global set title=?, badges=?, owned_titles=?, "
                                      "owned_badges=?, background=? where user=?",
                                      (self.titles[u],
                                       ",".join(self.badges[u]),
                                       ",".join(self.owned_titles[u]),
                                       ",".join(self.owned_badges[u]),
                                       self.backgrounds[u],
                                       u))
            await self.db.commit()
        async with self.guild_currency_lock:
            logging.log(15, "guild_cur:flush:-got lock")
            for guild, users in self.changed_guild_currency.items():
                for u in users:
                    currency = self.guild_currency[guild][u]
                    logging.log(15, f"guild_cur:flush:-checking user {self.bot.get_user(u)}")
                    a = await self.db.execute("SELECT * from guild_currency where guild = ? and user=?",
                                              (guild, u))
                    if not await a.fetchall():
                        logging.log(15, f"guild_cur:flush:-adding user {self.bot.get_user(u)}")
                        await self.db.execute("INSERT INTO guild_currency (user, guild, amount) values (?,?,?)",
                                              (u, guild, 0))
                    logging.log(15, f"guild_cur:flush:-updating user {self.bot.get_user(u)}")
                    await self.db.execute("UPDATE guild_currency set amount=? where user=? and guild=?",
                                          (currency, u, guild))
            await self.db.commit()
            self.changed_guild_currency = {}
        async with self.currency_gain_lock:
            for g in self.changed_currency_gains:
                a = await self.db.execute("SELECT * from currency_gains where guild=?",
                                          (g,))
                if not await a.fetchall():
                    await self.db.execute("insert into currency_gains (guild, gain) "
                                          "values (?,?)", (g, 0))
                await self.db.execute("update currency_gains set gain=? where guild=?",
                                      (self.currency_gains[g], g))
            await self.db.commit()
            self.changed_currency_gains = []

    async def lookup_punishments(self, user: int) -> List[_Punishment]:
        cursor = await self.db.execute("SELECT * from punishments where user=?", (user,))
        punishments = await cursor.fetchall()
        return [
            _Punishment(
                *p[:5],
                time=datetime.datetime.fromtimestamp(p[5])
            )
            for p in punishments
        ]

    async def add_punishment(self, user: int, guild: int, staff: int, typ: int,
                             reason: str = None):
        await self.db.execute("INSERT INTO punishments "
                              "(user, guild, staff, type, reason, timestamp) values"
                              "(?,?,?,?,?,?)",
                              (user, guild, staff, typ, reason, datetime.datetime.now().timestamp())
                              )
        await self.db.commit()

    async def add_user_ban(self, user: int, ctx: aoi.AoiContext, reason: str = None):
        await self.add_punishment(user, ctx.guild.id, ctx.author.id, PunishmentType.BAN, reason)

    async def add_user_mute(self, user: int, ctx: aoi.AoiContext, reason: str = None):
        await self.add_punishment(user, ctx.guild.id, ctx.author.id, PunishmentType.MUTE, reason)

    async def add_user_warn(self, user: int, ctx: aoi.AoiContext, reason: str = None):
        await self.add_punishment(user, ctx.guild.id, ctx.author.id, PunishmentType.WARN, reason)

    async def add_user_kick(self, user: int, ctx: aoi.AoiContext, reason: str = None):
        await self.add_punishment(user, ctx.guild.id, ctx.author.id, PunishmentType.KICK, reason)

    async def guild_setting(self, guild: int) -> _GuildSetting:
        if guild not in self.guild_settings:
            await self.db.execute("INSERT INTO guild_settings (Guild) values (?)", (guild,))
            await self.db.commit()
            self.guild_settings[guild] = _GuildSetting(
                ok_color=0x00aa00,
                error_color=0xaa0000,
                info_color=0x0000aa,
                perm_errors=True
            )
            self.prefixes[guild] = ","
        return self.guild_settings[guild]

    async def set_ok_color(self, guild: int, value: str):
        await self.db.execute(f"UPDATE guild_settings SET OkColor=? WHERE Guild=?", (value, guild))
        await self.db.commit()
        self.guild_settings[guild].ok_color = int(value, 16)

    async def set_error_color(self, guild: int, value: str):
        await self.db.execute(f"UPDATE guild_settings SET ErrorColor=? WHERE Guild=?", (value, guild))
        await self.db.commit()
        self.guild_settings[guild].error_color = int(value, 16)

    async def set_info_color(self, guild: int, value: str):
        await self.db.execute(f"UPDATE guild_settings SET InfoColor=? WHERE Guild=?", (value, guild))
        await self.db.commit()
        self.guild_settings[guild].info_color = int(value, 16)

    async def set_prefix(self, guild: int, prefix: str):
        await self.db.execute(f"UPDATE guild_settings SET Prefix=? WHERE Guild=?", (prefix, guild))
        await self.db.commit()
        self.prefixes[guild] = prefix

    async def get_permissions(self, guild: int):
        if guild not in self.perm_chains:
            await self.db.execute("INSERT INTO permissions (guild) values (?)", (guild,))
            await self.db.commit()
            self.perm_chains[guild] = ["asm enable"]
        return [s for s in self.perm_chains[guild]]

    async def set_permissions(self, guild: int, perms: List[str]):
        self.perm_chains[guild] = [s for s in perms]
        await self.db.execute("UPDATE permissions SET permissions=? WHERE guild=?",
                              (";".join(perms), guild))

    async def add_permission(self, guild: int, perm: str):
        logging.info(f"db:adding permission {guild}:{perm}")
        self.perm_chains[guild].append(perm)
        await self.db.execute("UPDATE permissions SET permissions=? WHERE guild=?",
                              (";".join(self.perm_chains[guild]), guild))
        await self.db.commit()

    async def remove_permission(self, guild: int, perm: int):
        del self.perm_chains[guild][perm]
        await self.db.execute("UPDATE permissions SET permissions=? WHERE guild=?",
                              (";".join(self.perm_chains[guild]), guild))
        await self.db.commit()

    async def clear_permissions(self, guild: int):
        self.perm_chains[guild] = ["asm enable"]
        await self.db.execute("UPDATE permissions SET permissions=? WHERE guild=?",
                              (";".join(self.perm_chains[guild]), guild))
        await self.db.commit()
