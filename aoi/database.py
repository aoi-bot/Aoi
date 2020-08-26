from __future__ import annotations

import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Dict, Optional, List, TYPE_CHECKING, Union

import aiosqlite
import discord
from aiosqlite import Connection
from discord.ext import tasks

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
        self.guild_settings: Dict[int, _GuildSetting] = {}
        self.prefixes: Dict[int, str] = {}
        self.perm_chains: Dict[int, List[str]] = {}
        self.bot = bot
        self.xp_lock = asyncio.Lock()
        self.xp: Dict[int, Dict[int, int]] = {}
        self.changed_xp: Dict[int, List[int]] = {}
        self.global_xp: Dict[int, int] = {}
        self.xp_cooldown = None

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
        self._cache_flush_loop.start()

    async def close(self):
        await self.cache_flush()
        await self.db.close()

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

    async def add_xp(self, msg: discord.Message):
        if msg.author.bot:
            return
        logging.log(15, f"xp:add:ensure xp entry for {msg.author}")
        await self.ensure_xp_entry(msg)
        logging.log(15, f"xp:add:waiting for lock")
        async with self.xp_lock:
            logging.log(15, f"xp:add:-got lock")
            self.xp[msg.guild.id][msg.author.id] += 3
            self.global_xp[msg.author.id] += 3
            if msg.author.id not in self.changed_xp[msg.guild.id]:
                logging.log(15, f"xp:add:-adding user change for {msg.author}")
                self.changed_xp[msg.guild.id].append(msg.author.id)
        logging.log(15, f"xp:add:-releasing lock")

    @tasks.loop(minutes=1)
    async def _cache_flush_loop(self):
        await self.cache_flush()

    async def cache_flush(self):
        logging.log(15, "xp:flush:waiting for lock")
        async with self.xp_lock:
            logging.log(15, "xp:flush:-got lock")
            print(self.changed_xp)
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
