from __future__ import annotations

import asyncio
import datetime
import logging
import sqlite3
from dataclasses import dataclass
from typing import Dict, Optional, List, TYPE_CHECKING, Union, Tuple

import aiosqlite
import discord
from aiosqlite import Connection
from discord.ext import tasks, commands

if TYPE_CHECKING:
    import aoi

SQL_STRING = """
CREATE TABLE IF NOT EXISTS "permissions" (
  "guild"  INTEGER NOT NULL,
  "permissions"  TEXT NOT NULL DEFAULT 'asm enable'
);;
CREATE TABLE IF NOT EXISTS "moderation" (
  "Guild"  TEXT NOT NULL,
  "MessageBurst"  TEXT DEFAULT '10 10;off',
  "MessageBurstPunishment"  TEXT DEFAULT 'mute 10',
  "FIlteredWords"  TEXT DEFAULT ';off',
  "FilteredWordsPunishment"  TEXT DEFAULT 'mute 10',
  "Characters"  TEXT DEFAULT '3000 10;off',
  "CharactersPunishment"  TEXT DEFAULT 'mute 10',
  "MuteRole"  INTEGER DEFAULT 0,
  "AutoModExemptChannels"  TEXT DEFAULT '',
  "AutoModExemptRole"  TEXT DEFAULT ''
);;
CREATE TABLE IF NOT EXISTS "punishments" (
  "user"  INTEGER NOT NULL,
  "guild"  INTEGER NOT NULL,
  "staff"  INTEGER NOT NULL,
  "type"  INTEGER NOT NULL,
  "reason"  TEXT,
  "timestamp"  INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "xp" (
  "user"  INTEGER NOT NULL,
  "guild"  INTEGER NOT NULL,
  "xp"  INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "guild_currency" (
  "guild"  INTEGER,
  "user"  INTEGER,
  "amount"  INTEGER
);;
CREATE TABLE IF NOT EXISTS "global_currency" (
  "user"  INTEGER,
  "amount"  INTEGER
);;
CREATE TABLE IF NOT EXISTS "user_global" (
  "user"  INTEGER,
  "title"  TEXT,
  "badges"  TEXT,
  "owned_titles"  TEXT,
  "owned_badges"  TEXT,
  "background"  TEXT
);;
CREATE TABLE IF NOT EXISTS "title_shop" (
  "id"  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
  "title"  TEXT,
  "cost"  INTEGER
);;
CREATE TABLE IF NOT EXISTS "guild_settings" (
  "Guild"  INTEGER NOT NULL,
  "OkColor"  TEXT NOT NULL DEFAULT '00aa00',
  "ErrorColor"  TEXT NOT NULL DEFAULT 'aa0000',
  "InfoColor"  TEXT NOT NULL DEFAULT '0000aa',
  "Prefix"  TEXT NOT NULL DEFAULT ',',
  "PermissionErrors"  INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY("Guild")
);;
CREATE TABLE IF NOT EXISTS "currency_gains" (
  "guild"  INTEGER,
  "gain"  INTEGER
);;
CREATE TABLE IF NOT EXISTS "guild_shop" (
  "guild"  INTEGER,
  "type"  TEXT,
  "data"  TEXT,
  "cost"  NUMERIC
);;
CREATE TABLE IF NOT EXISTS "badges" (
  "id"  INTEGER NOT NULL,
  "user"  INTEGER NOT NULL,
  "image"  BLOB NOT NULL,
  "price"  INTEGER NOT NULL,
  PRIMARY KEY("id")
);;
CREATE TABLE IF NOT EXISTS "messages" (
  "guild"  INTEGER NOT NULL,
  "welcome"  TEXT NOT NULL,
  "welcome_channel"  INTEGER NOT NULL,
  "welcome_delete"  INTEGER NOT NULL,
  "goodbye"  TEXT NOT NULL,
  "goodbye_channel"  INTEGER NOT NULL,
  "goodbye_delete"  INTEGER NOT NULL,
  PRIMARY KEY("guild")
);;
CREATE TABLE IF NOT EXISTS "autorole" (
  "guild"  INTEGER NOT NULL,
  "roles"  TEXT
)
"""


@dataclass
class _GuildSetting:
    ok_color: int
    error_color: int
    info_color: int
    perm_errors: bool


@dataclass(frozen=True)
class _RoleShopItem:
    type: str
    data: str
    cost: int


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


@dataclass()
class _Message:
    message: str
    channel: int
    delete: int


class AoiDatabase:
    # region # Database core
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
        self.guild_shop_lock = asyncio.Lock()
        self.messages_lock = asyncio.Lock()

        self.xp: Dict[int, Dict[int, int]] = {}
        self.changed_xp: Dict[int, List[int]] = {}
        self.global_currency: Dict[int, int] = {}
        self.changed_global_currency: List[int] = []
        self.messages: Dict[int, Tuple[_Message, _Message]] = {}
        self.global_xp: Dict[int, int] = {}
        self.guild_currency: Dict[int, Dict[int, int]] = {}
        self.changed_guild_currency: Dict[int, List[int]] = {}
        self.currency_gains: Dict[int, int] = {}
        self.changed_currency_gains: List[int] = []
        self.changed_guild_shop: List[int] = []
        self.changed_messages: List[int] = []
        self.auto_roles: Dict[int, List[int]] = {}

        self.titles: Dict[int, str] = {}
        self.owned_titles: Dict[int, List[str]] = {}
        self.badges: Dict[int, List[str]] = {}
        self.owned_badges: Dict[int, List[str]] = {}
        self.backgrounds: Dict[int, str] = {}
        self.changed_global_users: List[int] = []

        self.guild_shop: Dict[int, List[_RoleShopItem]] = {}

        self.xp_cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 180.0, commands.BucketType.member)
        self.global_currency_cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 60.0, commands.BucketType.user)

    async def load(self):  # noqa: C901
        self.bot.logger.info("database:Connecting to database")
        self.db = await aiosqlite.connect("database.db")
        [await self.db.execute(_) for _ in SQL_STRING.split(";;")]
        await self.db.commit()
        self.bot.logger.info("database:Loading database into memory")
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
        self.bot.logger.info("database:Database loaded")

        cursor = await self.db.execute("SELECT * from messages")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.messages[r[0]] = (
                _Message(*r[1:4]),
                _Message(*r[4:7])
            )

        # load guilds that dont exist in the database
        for i in self.bot.guilds:
            await self.guild_setting(i.id)
            await self.get_permissions(i.id)

        await self.cache_flush()

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

        # load auto roles
        cursor = await self.db.execute("SELECT * from autorole")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.auto_roles[r[0]] = [int(x) for x in r[1].split(",")]

        cursor = await self.db.execute("SELECT * from guild_shop")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            if r[0] not in self.guild_shop:
                self.guild_shop[r[0]] = []
            self.guild_shop[r[0]].append(_RoleShopItem(*r[1:]))

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

    @tasks.loop(minutes=1)
    async def _cache_flush_loop(self):
        await self.cache_flush()

    async def cache_flush(self):  # noqa: C901
        self.bot.logger.log(self.bot.TRACE, "xp:flush:waiting for lock")
        async with self.xp_lock:
            self.bot.logger.log(self.bot.TRACE, "xp:flush:-got lock")
            for guild, users in self.changed_xp.items():
                for u in users:
                    xp = self.xp[guild][u]
                    self.bot.logger.log(self.bot.TRACE, f"xp:flush:-checking user {self.bot.get_user(u)}")
                    a = await self.db.execute("SELECT * from xp where guild = ? and user=?", (guild, u))
                    if not await a.fetchall():
                        self.bot.logger.log(self.bot.TRACE, f"xp:flush:-adding user {self.bot.get_user(u)}")
                        await self.db.execute("INSERT INTO xp (user, guild, xp) values (?,?,?)", (u, guild, 0))
                    self.bot.logger.log(self.bot.TRACE, f"xp:flush:-updating user {self.bot.get_user(u)}")
                    await self.db.execute("UPDATE xp set xp=? where user=? and guild=?", (xp, u, guild))
            await self.db.commit()
            self.changed_xp = {}
        self.bot.logger.log(self.bot.TRACE, "xp:flush:released")
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
            self.bot.logger.log(self.bot.TRACE, "guild_cur:flush:-got lock")
            for guild, users in self.changed_guild_currency.items():
                for u in users:
                    currency = self.guild_currency[guild][u]
                    self.bot.logger.log(self.bot.TRACE, f"guild_cur:flush:-checking user {self.bot.get_user(u)}")
                    a = await self.db.execute("SELECT * from guild_currency where guild = ? and user=?",
                                              (guild, u))
                    if not await a.fetchall():
                        self.bot.logger.log(self.bot.TRACE, f"guild_cur:flush:-adding user {self.bot.get_user(u)}")
                        await self.db.execute("INSERT INTO guild_currency (user, guild, amount) values (?,?,?)",
                                              (u, guild, 0))
                    self.bot.logger.log(self.bot.TRACE, f"guild_cur:flush:-updating user {self.bot.get_user(u)}")
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
        async with self.guild_shop_lock:
            for guild in self.changed_guild_shop:
                await self.db.execute("DELETE FROM guild_shop WHERE guild=?", (guild,))
                for shop_item in self.guild_shop[guild]:
                    await self.db.execute("INSERT INTO guild_shop (guild, type, data, cost) values (?,?,?,?)",
                                          (guild, shop_item.type, shop_item.data, shop_item.cost))
            await self.db.commit()

        async with self.messages_lock:
            for guild in self.changed_messages:
                await self.db.execute("delete from messages where guild=?", (guild,))
                await self.db.execute("INSERT INTO messages values (?,?,?,?,?,?,?)",
                                      (guild,
                                       self.messages[guild][0].message,
                                       self.messages[guild][0].channel or 0,
                                       self.messages[guild][0].delete or 0,
                                       self.messages[guild][1].message,
                                       self.messages[guild][1].channel or 0,
                                       self.messages[guild][1].delete or 0,
                                       ))
            self.changed_messages = []

    # endregion

    # region # Auto roles

    async def add_auto_role(self, guild: discord.Guild, role: discord.Role):
        if guild.id not in self.auto_roles:
            self.auto_roles[guild.id] = [role.id]
        elif role.id not in self.auto_roles[guild.id]:
            self.auto_roles[guild.id].append(role.id)
        # immediately write to database
        a = await self.db.execute("select * from autorole where guild=?", (guild.id,))
        if not await a.fetchall():
            await self.db.execute("insert into autorole (guild, roles) values (?,?)",
                                  (guild.id, ",".join(map(str, self.auto_roles[guild.id]))))
        else:
            await self.db.execute("update autorole set roles=? where guild=?",
                                  (",".join(map(str, self.auto_roles[guild.id])), guild.id))
        await self.db.commit()

    async def del_auto_role(self, guild: discord.Guild, role: int):
        if guild.id in self.auto_roles and role in self.auto_roles[guild.id]:
            self.auto_roles[guild.id].remove(role)
        # immediately write to database
        a = await self.db.execute("select * from autorole where guild=?", (guild.id,))
        if not await a.fetchall():
            await self.db.execute("insert into autorole (guild, roles) values (?,?)",
                                  (guild.id, ",".join(map(str, self.auto_roles[guild.id]))))
        else:
            await self.db.execute("update autorole set roles=? where guild=?",
                                  (",".join(map(str, self.auto_roles[guild.id])), guild.id))
        await self.db.commit()

    # endregion

    # region # Guild shop

    async def ensure_guild_shop(self, guild: discord.Guild) -> None:
        if guild.id not in self.guild_shop:
            async with self.guild_shop_lock:
                self.guild_shop[guild.id] = []
                if guild.id not in self.changed_guild_shop:
                    self.changed_guild_shop.append(guild.id)

    async def get_guild_shop(self, guild: discord.Guild) -> List[_RoleShopItem]:
        await self.ensure_guild_shop(guild)
        return self.guild_shop[guild.id]

    async def add_guild_shop_item(self, guild: discord.Guild, typ: str, data: str, cost: int) -> None:
        await self.ensure_guild_shop(guild)
        async with self.guild_shop_lock:
            self.guild_shop[guild.id].append(_RoleShopItem(typ, data, cost))
            if guild.id not in self.changed_guild_shop:
                self.changed_guild_shop.append(guild.id)

    async def del_guild_shop_item(self, guild: discord.Guild, typ: str, data: str):
        await self.ensure_guild_shop(guild)
        for i in self.guild_shop[guild.id]:
            if i.data == data and i.type == typ:
                found = i
                break
        else:
            raise commands.CommandError("Guild shop item does not exist")
        async with self.guild_shop_lock:
            if guild.id not in self.changed_guild_shop:
                self.changed_guild_shop.append(guild.id)
            self.guild_shop[guild.id].remove(found)

    # region # Helper Methods

    async def add_guild_shop_role(self, guild: discord.Guild, role: discord.Role, cost: int) -> None:
        await self.add_guild_shop_item(guild, "role", str(role.id), cost)

    # endregion

    # endregion

    # region # Currency gain

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

    # endregion

    # region # User

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

    # endregion

    # region # Guild currency

    async def ensure_guild_currency_entry(self, member: discord.Member):
        self.bot.logger.log(self.bot.TRACE, "guild_cur:ensure:waiting for lock")
        async with self.guild_currency_lock:
            self.bot.logger.log(self.bot.TRACE, "guild_cur:ensure:-got lock")
            if member.guild.id not in self.guild_currency:
                self.guild_currency[member.guild.id] = {}
            if member.id not in self.guild_currency[member.guild.id]:
                self.guild_currency[member.guild.id][member.id] = 0
            if member.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[member.guild.id] = []
            if member.id not in self.changed_guild_currency[member.guild.id]:
                self.changed_guild_currency[member.guild.id].append(member.id)
        self.bot.logger.log(self.bot.TRACE, f"guild_cur:ensure:-releasing lock")

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

    # endregion

    # region # Global currency

    async def get_global_currency(self, member: discord.Member):
        await self.ensure_global_currency_entry(member)
        return self.global_currency[member.id]

    async def award_global_currency(self, member: discord.Member, amount: int):
        async with self.global_currency_lock:
            self.global_currency[member.id] = self.global_currency.get(member.id, 0) + amount
            if member.id not in self.changed_global_currency:
                self.changed_global_currency.append(member.id)

    async def ensure_global_currency_entry(self, member: discord.Member):
        async with self.global_currency_lock:
            if member.id not in self.global_currency:
                self.global_currency[member.id] = 0
                if member.id not in self.changed_global_currency:
                    self.changed_global_currency.append(member.id)

    async def add_global_currency(self, msg: discord.Message):
        if self.global_currency_cooldown.get_bucket(msg).update_rate_limit():
            return
        async with self.global_currency_lock:
            self.global_currency[msg.author.id] = self.global_currency.get(msg.author.id, 0) + 1
            if msg.author.id not in self.changed_global_currency:
                self.changed_global_currency.append(msg.author.id)

    # endregion

    # region # XP

    async def ensure_xp_entry(self, msg: Union[discord.Message, discord.Member]):
        if isinstance(msg, discord.Message):
            guild_id = msg.guild.id
            user_id = msg.author.id
        else:
            guild_id = msg.guild.id
            user_id = msg.id
        self.bot.logger.log(self.bot.TRACE, "xp:ensure:waiting for lock")
        async with self.xp_lock:
            self.bot.logger.log(self.bot.TRACE, "xp:ensure:-got lock")
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
        self.bot.logger.log(self.bot.TRACE, f"xp:ensure:-releasing lock")

    async def add_xp(self, msg: discord.Message):
        if msg.author.bot:
            return
        if self.xp_cooldown.get_bucket(msg).update_rate_limit():
            return
        self.bot.logger.log(self.bot.TRACE, f"xp:add:ensure xp entry for {msg.author}")
        await self.ensure_xp_entry(msg)
        c = 0
        for i in msg.guild.members:
            if not i.bot:
                c += 1
            if c == 3:
                break
        if c < 3:
            return
        self.bot.logger.log(self.bot.TRACE, f"xp:add:waiting for lock")
        async with self.xp_lock:
            self.bot.logger.log(self.bot.TRACE, f"xp:add:-got lock")
            self.xp[msg.guild.id][msg.author.id] += 3
            self.global_xp[msg.author.id] += 3
            if msg.author.id not in self.changed_xp[msg.guild.id]:
                self.bot.logger.log(self.bot.TRACE, f"xp:add:-adding user change for {msg.author}")
                self.changed_xp[msg.guild.id].append(msg.author.id)
        self.bot.logger.log(self.bot.TRACE, f"xp:add:-releasing lock")
        await self.ensure_currency_gain(msg.guild)
        await self.ensure_guild_currency_entry(msg.author)
        async with self.guild_currency_lock:
            self.guild_currency[msg.guild.id][msg.author.id] += self.currency_gains[msg.guild.id]
            if msg.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[msg.guild.id] = []
            if msg.author.id not in self.changed_guild_currency[msg.guild.id]:
                self.changed_guild_currency[msg.guild.id].append(msg.author.id)

    # endregion

    # region # Moderation

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

    # endregion

    # region # Config

    async def _auto_messages(self, guild: int) -> Tuple[_Message, _Message]:
        if guild not in self.messages:
            async with self.messages_lock:
                try:
                    await self.db.execute("INSERT INTO messages values (?,?,?,?,?,?,?)",
                                          (guild,
                                           "&user_name; has joined the server",
                                           0,
                                           0,
                                           "&user_name; has left the server",
                                           0,
                                           0
                                           ))
                except sqlite3.IntegrityError:
                    pass
                await self.db.commit()
                self.messages[guild] = (
                    _Message("&user_name; has joined the server", 0, 0),
                    _Message("&user_name; has left the server", 0, 0)
                )
        return self.messages[guild]

    async def get_welcome_message(self, guild: int) -> _Message:
        return (await self._auto_messages(guild))[0]

    async def get_goodbye_message(self, guild: int) -> _Message:
        return (await self._auto_messages(guild))[1]

    async def set_welcome_message(self, guild: int, *,
                                  message: str = None,
                                  channel: discord.TextChannel = None,
                                  delete: int = None):
        async with self.messages_lock:
            if message is not None:
                self.messages[guild][0].message = message
            if channel is not None:
                self.messages[guild][0].channel = channel.id
            if delete is not None:
                self.messages[guild][0].delete = delete
            if guild not in self.changed_messages:
                self.changed_messages.append(guild)

    async def set_goodbye_message(self, guild: int, *,
                                  message: str = None,
                                  channel: discord.TextChannel = None,
                                  delete: int = None):
        async with self.messages_lock:
            if message is not None:
                self.messages[guild][1].message = message
            if channel is not None:
                self.messages[guild][1].channel = channel.id
            if delete is not None:
                self.messages[guild][1].delete = delete
            if guild not in self.changed_messages:
                self.changed_messages.append(guild)

    async def guild_setting(self, guild: int) -> _GuildSetting:
        if guild not in self.guild_settings:
            try:
                await self.db.execute("INSERT INTO guild_settings (Guild) values (?)", (guild,))
            except sqlite3.IntegrityError:
                self.bot.logger.warning(f"Passing IntegrityError for guild {guild}")
                pass
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
        self.bot.logger.info(f"db:adding permission {guild}:{perm}")
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

    # endregion
