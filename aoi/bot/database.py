from __future__ import annotations

import asyncio
import datetime
import logging
import sqlite3
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

import aiosqlite
import discord
import hikari
from aiosqlite import Connection
from discord.ext import commands, tasks

from aoi.bot.database_models import (AoiMessageModel, GuildSettingModel,
                                     PunishmentModel, PunishmentTypeModel,
                                     RoleShopItemModel, TimedPunishmentModel)

if TYPE_CHECKING:
    from aoi import bot

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
);;
CREATE TABLE IF NOT EXISTS "rero" (
  "guild" INTEGER NOT NULL,
  "channel" INTEGER NOT NULL,
  "message" INTEGER NOT NULL,
  "emoji" TEXT NOT NULL,
  "role" INTEGER NOT NULL,
  "time" INTEGER NOT NULL,
  "onetime" INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "selfrole" (
  "guild" INTEGER NOT NULL,
  "role" INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "roletriggers" (
  "guild" INTEGER NOT NULL,
  "role" INTEGER NOT NULL,
  "channel" INTEGER NOT NULL,
  "message" TEXT NOT NULL,
  "type" TEXT NOT NULL
);;
CREATE TABLE IF NOT EXISTS "warnpunish" (
  "guild" INTEGER NOT NULL,
  "level" INTEGER NOT NULL,
  "action" TEXT NOT NULL
);;
CREATE TABLE IF NOT EXISTS "current_punishments" (
  "id" INTEGER NOT NULL,
  "guild" INTEGER NOT NULL,
  "role" INTEGER NOT NULL,
  "end" INTEGER NOT NULL,
  "ismute" INTEGER NOT NULL,
  "user" INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "blacklist" (
  "user" INTEGER NOT NULL
);;
CREATE INDEX IF NOT EXISTS idx_blacklist ON blacklist (user);;
CREATE TABLE IF NOT EXISTS "slowmode" (
  "channel" INTEGER NOT NULL UNIQUE,
  "seconds" INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "last_messages" (
  "channel" INTEGER,
  "user" INTEGER NOT NULL,
  "timestamp" INTEGER NOT NULL
);;
CREATE TABLE IF NOT EXISTS "patreon" (
  "user" INTEGER NOT NULL PRIMARY KEY UNIQUE,
  "last_claim" TEXT NOT NULL
);;
CREATE INDEX IF NOT EXISTS idx_patreon on patreon (user);;
CREATE TABLE IF NOT EXISTS "quotes" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user" INTEGER NOT NULL,
  "guild" INTEGER NOT NULL,
  "name" TEXT NOT NULL,
  "content" TEXT NOT NULL
);;
CREATE INDEX IF NOT EXISTS idx_quotes on quotes (id);;
CREATE TABLE IF NOT EXISTS "alias" (
  "guild" INTEGER NOT NULL,
  "from" TEXT NOT NULL,
  "to" TEXT NOT NULL
);;
CREATE TABLE IF NOT EXISTS roleplay (
  "user" INTEGER NOT NULL,
  "times" TEXT NOT NULL default "{}"
);;
"""

MIGRATIONS = {
    1: """
ALTER TABLE guild_settings ADD COLUMN currency_img TEXT;
ALTER TABLE guild_settings ADD COLUMN currency_chance INTEGER DEFAULT 4;
ALTER TABLE guild_settings ADD COLUMN currency_max INTEGER DEFAULT 10;
ALTER TABLE guild_settings ADD COLUMN currency_min INTEGER DEFAULT 8;
ALTER TABLE guild_settings ADD COLUMN currency_gen_channels TEXT DEFAULT '';
    """,
    2: """
ALTER TABLE guild_settings ADD COLUMN delete_on_ban INTEGER DEFAULT 1;
    """,
    3: """
ALTER TABLE guild_settings ADD COLUMN reply_embeds INTEGER DEFAULT 1;
    """,
    4: """
ALTER TABLE punishments ADD COLUMN cleared INTEGER DEFAULT 0;
ALTER TABLE punishments ADD COLUMN cleared_by INTEGER DEFAULT 0;
    """,
}


class AoiDatabase:
    # region # Database core
    def __init__(self, aoi: hikari.GatewayBot):
        self.bot = aoi
        self.conn: Optional[Connection] = None
        self.logger = logging.getLogger("database")

        self.guild_settings: Dict[int, GuildSettingModel] = {}
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
        self.messages: Dict[int, Tuple[AoiMessageModel, AoiMessageModel]] = {}
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

        self.guild_shop: Dict[int, List[RoleShopItemModel]] = {}

        self.blacklisted: List[int] = []

        self.xp_cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 180.0, commands.BucketType.member
        )
        self.global_currency_cooldown = commands.CooldownMapping.from_cooldown(
            1.0, 60.0, commands.BucketType.user
        )

    async def perform_migrations(self):
        version = (await (await self.conn.execute("pragma user_version")).fetchone())[0]
        self.logger.info(f"database:Version {version} found")
        for i in sorted(MIGRATIONS.keys()):
            if i > version:
                self.logger.info(f"database:Upgrading to version {i + 1}")
                [await self.conn.execute(_) for _ in MIGRATIONS[i].splitlines() if _]
                await self.conn.execute(f"pragma user_version={i}")
                await self.conn.commit()

    async def load(self):  # noqa: C901
        self.logger.info("database:Connecting to database")
        self.conn = await aiosqlite.connect("database.db")
        [await self.conn.execute(_) for _ in SQL_STRING.split(";;")]
        await self.conn.commit()
        await self.perform_migrations()

        self.logger.info("database:Loading database into memory")
        cursor = await self.conn.execute("SELECT * from guild_settings")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.guild_settings[r[0]] = GuildSettingModel.from_row(r)
            self.prefixes[r[0]] = r[4]
        cursor = await self.conn.execute("SELECT * from permissions")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.perm_chains[r[0]] = r[1].split(";")
        self.logger.info("database:Database loaded")

        rows = await self.conn.execute_fetchall("select * from blacklist")
        self.blacklisted = [r[0] for r in rows]

        cursor = await self.conn.execute("SELECT * from messages")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.messages[r[0]] = (AoiMessageModel(*r[1:4]), AoiMessageModel(*r[4:7]))

        # load guilds that don't exist in the database
        for i in self.bot.cache.get_guilds_view().values():
            await self.guild_setting(i.id)
            await self.get_permissions(i.id)

        await self.cache_flush()

        cursor = await self.conn.execute("SELECT * from xp")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            if r[1] not in self.xp:
                self.xp[r[1]] = {}
            self.xp[r[1]][r[0]] = r[2]
            self.global_xp[r[0]] = self.global_xp.get(r[0], 0) + r[2]

        # load global currency
        cursor = await self.conn.execute("SELECT * from global_currency")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.global_currency[r[0]] = r[1]

        # load auto roles
        cursor = await self.conn.execute("SELECT * from autorole")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.auto_roles[r[0]] = [int(x) for x in r[1].split(",") if x]

        cursor = await self.conn.execute("SELECT * from guild_shop")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            if r[0] not in self.guild_shop:
                self.guild_shop[r[0]] = []
            self.guild_shop[r[0]].append(RoleShopItemModel(*r[1:]))

        cursor = await self.conn.execute("SELECT * from user_global")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.titles[r[0]] = r[1]
            self.badges[r[0]] = r[2].split(",")
            self.owned_titles[r[0]] = r[3].split(",")
            self.owned_badges[r[0]] = r[4].split(",")
            self.backgrounds[r[0]] = r[5]

        cursor = await self.conn.execute("select * from currency_gains")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.currency_gains[r[0]] = r[1]

        for i in self.bot.cache.get_guilds_view().values():
            await self.ensure_currency_gain(i)

        cursor = await self.conn.execute("select * from guild_currency")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            if r[0] not in self.guild_currency:
                self.guild_currency[r[0]] = {}
            self.guild_currency[r[0]][r[1]] = r[2]

        for i in self.bot.cache.get_guilds_view().values():
            for m in i.get_members().values():
                await self.ensure_user_entry(m)

        self._cache_flush_loop.start()

    async def close(self):
        await self.cache_flush()
        await self.conn.close()

    @tasks.loop(minutes=1)
    async def _cache_flush_loop(self):
        await self.cache_flush()

    async def cache_flush(self):  # noqa: C901

        async with self.xp_lock:

            for guild, users in self.changed_xp.items():
                for u in users:
                    xp = self.xp[guild][u]

                    a = await self.conn.execute(
                        "SELECT * from xp where guild = ? and user=?", (guild, u)
                    )
                    if not await a.fetchall():
                        await self.conn.execute(
                            "INSERT INTO xp (user, guild, xp) values (?,?,?)",
                            (u, guild, 0),
                        )

                    await self.conn.execute(
                        "UPDATE xp set xp=? where user=? and guild=?", (xp, u, guild)
                    )
            await self.conn.commit()
            self.changed_xp = {}

        async with self.global_currency_lock:
            for u in self.changed_global_currency:
                a = await self.conn.execute(
                    "SELECT * from global_currency where user=?", (u,)
                )
                if not await a.fetchall():
                    await self.conn.execute(
                        "insert into global_currency (user, amount) " "values (?,?)",
                        (u, 0),
                    )
                await self.conn.execute(
                    "update global_currency set amount=? where user=?",
                    (self.global_currency[u], u),
                )
            await self.conn.commit()
            self.changed_global_currency = []
        async with self.title_lock:
            for u in self.changed_global_users:
                a = await self.conn.execute(
                    "select * from user_global where user=?", (u,)
                )
                if not await a.fetchall():
                    await self.conn.execute(
                        "insert into user_global (user, title, badges, owned_titles, owned_badges,"
                        "background) "
                        "values (?,?,?,?,?,?)",
                        (u, "", "", "", "", ""),
                    )
                await self.conn.execute(
                    "update user_global set title=?, badges=?, owned_titles=?, "
                    "owned_badges=?, background=? where user=?",
                    (
                        self.titles[u],
                        ",".join(self.badges[u]),
                        ",".join(self.owned_titles[u]),
                        ",".join(self.owned_badges[u]),
                        self.backgrounds[u],
                        u,
                    ),
                )
            await self.conn.commit()
        async with self.guild_currency_lock:

            for guild, users in self.changed_guild_currency.items():
                for u in users:
                    currency = self.guild_currency[guild][u]

                    a = await self.conn.execute(
                        "SELECT * from guild_currency where guild = ? and user=?",
                        (guild, u),
                    )
                    if not await a.fetchall():
                        await self.conn.execute(
                            "INSERT INTO guild_currency (user, guild, amount) values (?,?,?)",
                            (u, guild, 0),
                        )

                    await self.conn.execute(
                        "UPDATE guild_currency set amount=? where user=? and guild=?",
                        (currency, u, guild),
                    )
            await self.conn.commit()
            self.changed_guild_currency = {}
        async with self.currency_gain_lock:
            for g in self.changed_currency_gains:
                a = await self.conn.execute(
                    "SELECT * from currency_gains where guild=?", (g,)
                )
                if not await a.fetchall():
                    await self.conn.execute(
                        "insert into currency_gains (guild, gain) " "values (?,?)",
                        (g, 0),
                    )
                await self.conn.execute(
                    "update currency_gains set gain=? where guild=?",
                    (self.currency_gains[g], g),
                )
            await self.conn.commit()
            self.changed_currency_gains = []

        async with self.guild_shop_lock:
            for guild in self.changed_guild_shop:
                await self.conn.execute(
                    "DELETE FROM guild_shop WHERE guild=?", (guild,)
                )
                for shop_item in self.guild_shop[guild]:
                    await self.conn.execute(
                        "INSERT INTO guild_shop (guild, type, data, cost) values (?,?,?,?)",
                        (guild, shop_item.type, shop_item.data, shop_item.cost),
                    )
            await self.conn.commit()

        async with self.messages_lock:
            for guild in self.changed_messages:
                await self.conn.execute("delete from messages where guild=?", (guild,))
                await self.conn.execute(
                    "INSERT INTO messages values (?,?,?,?,?,?,?)",
                    (
                        guild,
                        self.messages[guild][0].message,
                        self.messages[guild][0].channel or 0,
                        self.messages[guild][0].delete or 0,
                        self.messages[guild][1].message,
                        self.messages[guild][1].channel or 0,
                        self.messages[guild][1].delete or 0,
                    ),
                )
            self.changed_messages = []
            await self.conn.commit()

    # endregion

    # region # Auto roles

    async def add_auto_role(self, guild: hikari.PartialGuild, role: discord.Role):
        if guild.id not in self.auto_roles:
            self.auto_roles[guild.id] = [role.id]
        elif role.id not in self.auto_roles[guild.id]:
            self.auto_roles[guild.id].append(role.id)
        # immediately write to database
        a = await self.conn.execute("select * from autorole where guild=?", (guild.id,))
        if not await a.fetchall():
            await self.conn.execute(
                "insert into autorole (guild, roles) values (?,?)",
                (guild.id, ",".join(map(str, self.auto_roles[guild.id]))),
            )
        else:
            await self.conn.execute(
                "update autorole set roles=? where guild=?",
                (",".join(map(str, self.auto_roles[guild.id])), guild.id),
            )
        await self.conn.commit()

    async def del_auto_role(self, guild: hikari.PartialGuild, role: int):
        if guild.id in self.auto_roles and role in self.auto_roles[guild.id]:
            self.auto_roles[guild.id].remove(role)
        # immediately write to database
        a = await self.conn.execute("select * from autorole where guild=?", (guild.id,))
        if not await a.fetchall():
            await self.conn.execute(
                "insert into autorole (guild, roles) values (?,?)",
                (guild.id, ",".join(map(str, self.auto_roles[guild.id]))),
            )
        else:
            await self.conn.execute(
                "update autorole set roles=? where guild=?",
                (",".join(map(str, self.auto_roles[guild.id])), guild.id),
            )
        await self.conn.commit()

    # endregion

    # region # Self roles

    async def get_self_roles(self, guild: hikari.PartialGuild) -> List[int]:
        return [
            a[0]
            for a in await self.conn.execute_fetchall(
                f"select role from selfrole where guild=?", (guild.id,)
            )
        ]

    async def add_self_role(
        self, guild: hikari.PartialGuild, role: discord.Role
    ) -> None:
        if role.id in await self.get_self_roles(guild):
            return
        await self.conn.execute(
            "insert into selfrole (guild, role) values (?,?)", (guild.id, role.id)
        )
        await self.conn.commit()

    async def remove_self_role(self, role: Union[discord.Role, int]) -> None:
        if isinstance(role, discord.Role):
            role = role.id
        await self.conn.execute("delete from selfrole where role=?", (role,))
        await self.conn.commit()

    # endregion

    # region # Guild shop

    async def ensure_guild_shop(self, guild: hikari.PartialGuild) -> None:
        if guild.id not in self.guild_shop:
            async with self.guild_shop_lock:
                self.guild_shop[guild.id] = []
                if guild.id not in self.changed_guild_shop:
                    self.changed_guild_shop.append(guild.id)

    async def get_guild_shop(
        self, guild: hikari.PartialGuild
    ) -> List[RoleShopItemModel]:
        await self.ensure_guild_shop(guild)
        return self.guild_shop[guild.id]

    async def add_guild_shop_item(
        self, guild: hikari.PartialGuild, typ: str, data: str, cost: int
    ) -> None:
        await self.ensure_guild_shop(guild)
        async with self.guild_shop_lock:
            self.guild_shop[guild.id].append(RoleShopItemModel(typ, data, cost))
            if guild.id not in self.changed_guild_shop:
                self.changed_guild_shop.append(guild.id)

    async def del_guild_shop_item(
        self, guild: hikari.PartialGuild, typ: str, data: str
    ):
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

    async def add_guild_shop_role(
        self, guild: hikari.PartialGuild, role: discord.Role, cost: int
    ) -> None:
        await self.add_guild_shop_item(guild, "role", str(role.id), cost)

    # endregion

    # endregion

    # region # Currency gain

    async def ensure_currency_gain(self, guild: hikari.PartialGuild):
        if guild.id not in self.currency_gains:
            async with self.currency_gain_lock:
                if guild.id not in self.changed_currency_gains:
                    self.changed_currency_gains.append(guild.id)
                self.currency_gains[guild.id] = 0

    async def set_currency_gain(self, guild: hikari.PartialGuild, new: int):
        await self.ensure_currency_gain(guild)
        async with self.currency_gain_lock:
            if guild.id not in self.changed_currency_gains:
                self.changed_currency_gains.append(guild.id)
            self.currency_gains[guild.id] = new

    async def get_currency_gain(self, guild: hikari.PartialGuild):
        await self.ensure_currency_gain(guild)
        return self.currency_gains[guild.id]

    # endregion

    # region # User

    async def ensure_user_entry(self, member: hikari.Member):
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

    async def get_titles(self, member: hikari.Member) -> Tuple[str, List[str]]:
        await self.ensure_user_entry(member)
        return self.titles[member.id], self.owned_titles[member.id]

    async def get_badges(self, member: hikari.Member) -> Tuple[List[str], List[str]]:
        await self.ensure_user_entry(member)
        return self.badges[member.id], self.owned_badges[member.id]

    async def add_title(self, member: hikari.Member, title: str):
        await self.ensure_user_entry(member)
        async with self.title_lock:
            self.owned_titles[member.id].append(title)
        await self.cache_flush()

    async def equip_title(self, member: hikari.Member, index: int):
        await self.ensure_user_entry(member)
        async with self.title_lock:
            self.titles[member.id] = self.owned_titles[member.id][index]
        await self.cache_flush()

    async def get_badges_titles(
        self, member: hikari.Member
    ) -> Tuple[str, List[str], List[str], List[str], str]:
        await self.ensure_user_entry(member)
        async with self.title_lock:
            if member.id not in self.titles:
                self.titles[member.id] = ""
                self.badges[member.id] = []
                self.owned_badges[member.id] = []
                self.owned_titles[member.id] = []
                await self.conn.execute(
                    "insert into user_global (user, title, badges, owned_titles, owned_badges) "
                    "values (?,?,?,?,?)",
                    (member.id, "", "", "", ""),
                )
                await self.conn.commit()
            return (
                self.titles[member.id],
                self.badges[member.id],
                self.owned_titles[member.id],
                self.owned_badges[member.id],
                self.backgrounds[member.id],
            )

    # endregion

    # region # Guild currency

    async def ensure_guild_currency_entry(self, member: hikari.Member):

        async with self.guild_currency_lock:

            if member.guild.id not in self.guild_currency:
                self.guild_currency[member.guild.id] = {}
            if member.id not in self.guild_currency[member.guild.id]:
                self.guild_currency[member.guild.id][member.id] = 0
            if member.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[member.guild.id] = []
            if member.id not in self.changed_guild_currency[member.guild.id]:
                self.changed_guild_currency[member.guild.id].append(member.id)

    async def get_guild_currency(self, member: hikari.Member) -> int:
        await self.ensure_guild_currency_entry(member)
        return self.guild_currency[member.guild.id][member.id]

    async def award_guild_currency(self, member: hikari.Member, amount: int):
        await self.ensure_guild_currency_entry(member)
        async with self.guild_currency_lock:
            self.guild_currency[member.guild.id][member.id] += amount
            if member.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[member.guild.id] = []
            if member.id not in self.changed_guild_currency[member.guild.id]:
                self.changed_guild_currency[member.guild.id].append(member.id)

    # endregion

    # region # Global currency

    async def get_global_currency(self, member: hikari.Member):
        await self.ensure_global_currency_entry(member)
        return self.global_currency[member.id]

    async def award_global_currency(self, member: hikari.Member, amount: int):
        async with self.global_currency_lock:
            self.global_currency[member.id] = (
                self.global_currency.get(member.id, 0) + amount
            )
            if member.id not in self.changed_global_currency:
                self.changed_global_currency.append(member.id)

    async def ensure_global_currency_entry(self, member: hikari.Member):
        async with self.global_currency_lock:
            if member.id not in self.global_currency:
                self.global_currency[member.id] = 0
                if member.id not in self.changed_global_currency:
                    self.changed_global_currency.append(member.id)

    async def add_global_currency(self, msg: discord.Message):
        if msg.author.id in self.blacklisted:
            return
        if self.global_currency_cooldown.get_bucket(msg).update_rate_limit():
            return
        async with self.global_currency_lock:
            self.global_currency[msg.author.id] = (
                self.global_currency.get(msg.author.id, 0) + 1
            )
            if msg.author.id not in self.changed_global_currency:
                self.changed_global_currency.append(msg.author.id)

    # endregion

    # region # XP

    async def ensure_xp_entry(self, msg: Union[discord.Message, hikari.Member]):
        if isinstance(msg, discord.Message):
            guild_id = msg.guild.id
            user_id = msg.author.id
        else:
            guild_id = msg.guild.id
            user_id = msg.id

        async with self.xp_lock:

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

    async def add_xp(self, msg: hikari.Message):  # noqa c901
        if msg.author.is_bot:
            return
        if msg.author.id in self.blacklisted:
            return
        if self.xp_cooldown.get_bucket(msg).update_rate_limit():
            return

        await self.ensure_xp_entry(msg)
        c = 0
        for i in msg.guild.members:
            if not i.bot:
                c += 1
            if c == 3:
                break
        if c < 3:
            return

        async with self.xp_lock:

            self.xp[msg.guild.id][msg.author.id] += 3
            self.global_xp[msg.author.id] += 3
            if msg.author.id not in self.changed_xp[msg.guild.id]:
                self.changed_xp[msg.guild.id].append(msg.author.id)

        await self.ensure_currency_gain(msg.guild)
        await self.ensure_guild_currency_entry(
            self.bot.cache.get_guild(msg.guild_id).get_member(msg.author.id)
        )
        async with self.guild_currency_lock:
            self.guild_currency[msg.guild.id][msg.author.id] += self.currency_gains[
                msg.guild.id
            ]
            if msg.guild.id not in self.changed_guild_currency:
                self.changed_guild_currency[msg.guild.id] = []
            if msg.author.id not in self.changed_guild_currency[msg.guild.id]:
                self.changed_guild_currency[msg.guild.id].append(msg.author.id)

    # endregion

    # region # Moderation

    async def lookup_punishments(self, user: int) -> List[PunishmentModel]:
        cursor = await self.conn.execute(
            "SELECT * from punishments where user=?", (user,)
        )
        punishments = await cursor.fetchall()
        return [
            PunishmentModel(
                *p[:5],
                time=datetime.datetime.fromtimestamp(p[5]),
                cleared=p[6],
                cleared_by=p[7],
            )
            for p in punishments
        ]

    async def add_punishment(
        self, user: int, guild: int, staff: int, typ: int, reason: str = None
    ):
        await self.conn.execute(
            "INSERT INTO punishments "
            "(user, guild, staff, type, reason, timestamp) values"
            "(?,?,?,?,?,?)",
            (user, guild, staff, typ, reason, datetime.datetime.now().timestamp()),
        )
        await self.conn.commit()

    async def add_user_ban(self, user: int, ctx: bot.AoiContext, reason: str = None):
        await self.add_punishment(
            user, ctx.guild.id, ctx.author.id, PunishmentTypeModel.BAN, reason
        )

    async def add_user_mute(self, user: int, ctx: bot.AoiContext, reason: str = None):
        await self.add_punishment(
            user, ctx.guild.id, ctx.author.id, PunishmentTypeModel.MUTE, reason
        )

    async def add_user_warn(self, user: int, ctx: bot.AoiContext, reason: str = None):
        await self.add_punishment(
            user, ctx.guild.id, ctx.author.id, PunishmentTypeModel.WARN, reason
        )

    async def add_user_kick(self, user: int, ctx: bot.AoiContext, reason: str = None):
        await self.add_punishment(
            user, ctx.guild.id, ctx.author.id, PunishmentTypeModel.KICK, reason
        )

    async def get_warnp(self, guild: int, warns: int) -> Optional[str]:
        rows = list(
            await self.conn.execute_fetchall(
                "select action from warnpunish where guild=? and level=?",
                (guild, warns),
            )
        )
        return rows[0][0] if rows else None

    async def set_warnp(self, guild: int, warns: int, action: str):
        await self.conn.execute(
            "delete from warnpunish where guild=? and level=?", (guild, warns)
        )
        await self.conn.execute(
            "insert into warnpunish (guild, level, action) values (?,?,?)",
            (guild, warns, action),
        )
        await self.conn.commit()

    async def del_warnp(self, guild: int, warns: int):
        await self.conn.execute(
            "delete from warnpunish where guild=? and level=?", (guild, warns)
        )
        await self.conn.commit()

    async def get_all_warnp(self, guild: int) -> List[Tuple[int, str]]:
        rows = list(
            await self.conn.execute_fetchall(
                "select level, action from warnpunish where guild=? order by level",
                (guild,),
            )
        )
        return list(map(tuple, rows))

    async def add_timed_punishment(
        self, guild: int, duration: datetime.timedelta, user: int, role: int, mute: bool
    ):
        await self.conn.execute(
            "insert into punishments (id, guild, end, user, role, ismute) values (?,?,?,?,?)",
            (
                datetime.datetime.now().utcnow(),
                guild,
                datetime.datetime.utcnow() + duration,
                user,
                role,
                1 if mute else 0,
            ),
        )
        await self.conn.commit()

    async def removed_timed_punishment(self, _id: int):
        await self.conn.execute("delete from punishments where id=?", (_id,))
        await self.conn.commit()

    async def load_backing_punishments(self) -> Dict[int, List[TimedPunishmentModel]]:
        rows = await self.conn.execute_fetchall("select * from punishments")
        punishments = {}
        for r in rows:
            _id, guild, role, end, ismute, user = *r[0:4], r[4] == 1, r[5]  # noqa
            if guild not in punishments:
                punishments[guild] = []
            punishments[guild].append(
                TimedPunishmentModel(_id, guild, role, end, ismute, user)
            )
        return punishments

    # endregion

    # region # Config

    async def _auto_messages(
        self, guild: int
    ) -> Tuple[AoiMessageModel, AoiMessageModel]:
        if guild not in self.messages:
            async with self.messages_lock:
                try:
                    await self.conn.execute(
                        "INSERT INTO messages values (?,?,?,?,?,?,?)",
                        (
                            guild,
                            "&user_name; has joined the server",
                            0,
                            0,
                            "&user_name; has left the server",
                            0,
                            0,
                        ),
                    )
                except sqlite3.IntegrityError:
                    pass
                await self.conn.commit()
                self.messages[guild] = (
                    AoiMessageModel("&user_name; has joined the server", 0, 0),
                    AoiMessageModel("&user_name; has left the server", 0, 0),
                )
        return self.messages[guild]

    async def get_welcome_message(self, guild: int) -> AoiMessageModel:
        return (await self._auto_messages(guild))[0]

    async def get_goodbye_message(self, guild: int) -> AoiMessageModel:
        return (await self._auto_messages(guild))[1]

    async def set_welcome_message(
        self,
        guild: int,
        *,
        message: str = None,
        channel: discord.TextChannel = None,
        delete: int = None,
    ):
        async with self.messages_lock:
            if message is not None:
                self.messages[guild][0].message = message
            if channel is not None:
                self.messages[guild][0].channel = channel.id
            if delete is not None:
                self.messages[guild][0].delete = delete
            if guild not in self.changed_messages:
                self.changed_messages.append(guild)

    async def set_goodbye_message(
        self,
        guild: int,
        *,
        message: str = None,
        channel: discord.TextChannel = None,
        delete: int = None,
    ):
        async with self.messages_lock:
            if message is not None:
                self.messages[guild][1].message = message
            if channel is not None:
                self.messages[guild][1].channel = channel.id
            if delete is not None:
                self.messages[guild][1].delete = delete
            if guild not in self.changed_messages:
                self.changed_messages.append(guild)

    async def guild_setting(self, guild: int) -> GuildSettingModel:
        if guild not in self.guild_settings:
            try:
                await self.conn.execute(
                    "INSERT INTO guild_settings (Guild) values (?)", (guild,)
                )
            except sqlite3.IntegrityError:
                self.logger.warning(f"Passing IntegrityError for guild {guild}")
            await self.conn.commit()
            self.guild_settings[guild] = GuildSettingModel()
            self.prefixes[guild] = ","
        return self.guild_settings[guild]

    async def set_currency_gen(self, guild: int, **kwargs):
        await self.guild_setting(guild)
        if "min_amt" in kwargs:
            self.guild_settings[guild].currency_min = kwargs["min_amt"]
            await self.conn.execute(
                "UPDATE guild_settings SET currency_min=? WHERE guild=?",
                (kwargs["min_amt"], guild),
            )
        if "max_amt" in kwargs:
            self.guild_settings[guild].currency_max = kwargs["min_amt"]
            await self.conn.execute(
                "UPDATE guild_settings SET currency_max=? WHERE guild=?",
                (kwargs["max_amt"], guild),
            )
        if "chance" in kwargs:
            self.guild_settings[guild].currency_chance = kwargs["chance"]
            await self.conn.execute(
                "UPDATE guild_settings SET currency_chance=? WHERE guild=?",
                (kwargs["chance"], guild),
            )
        await self.conn.commit()

    async def add_currency_channel(self, channel: discord.TextChannel):
        await self.guild_setting(channel.guild.id)
        if (
            channel.id
            not in self.guild_settings[channel.guild.id].currency_gen_channels
        ):
            self.guild_settings[channel.guild.id].currency_gen_channels.append(
                channel.id
            )
        await self.conn.execute(
            f"UPDATE guild_settings SET currency_gen_channels=? WHERE Guild=?",
            (
                ",".join(
                    map(
                        str, self.guild_settings[channel.guild.id].currency_gen_channels
                    )
                ),
                channel.guild.id,
            ),
        )
        await self.conn.commit()

    async def remove_currency_channel(self, channel: discord.TextChannel):
        await self.guild_setting(channel.guild.id)
        if channel.id in self.guild_settings[channel.guild.id].currency_gen_channels:
            self.guild_settings[channel.guild.id].currency_gen_channels.remove(
                channel.id
            )
        await self.conn.execute(
            f"UPDATE guild_settings SET currency_gen_channels=? WHERE Guild=?",
            (
                ",".join(
                    map(
                        str, self.guild_settings[channel.guild.id].currency_gen_channels
                    )
                ),
                channel.guild.id,
            ),
        )
        await self.conn.commit()

    async def set_ok_color(self, guild: int, value: str):
        await self.conn.execute(
            f"UPDATE guild_settings SET OkColor=? WHERE Guild=?", (value, guild)
        )
        await self.conn.commit()
        self.guild_settings[guild].ok_color = int(value, 16)

    async def set_error_color(self, guild: int, value: str):
        await self.conn.execute(
            f"UPDATE guild_settings SET ErrorColor=? WHERE Guild=?", (value, guild)
        )
        await self.conn.commit()
        self.guild_settings[guild].error_color = int(value, 16)

    async def set_info_color(self, guild: int, value: str):
        await self.conn.execute(
            f"UPDATE guild_settings SET InfoColor=? WHERE Guild=?", (value, guild)
        )
        await self.conn.commit()
        self.guild_settings[guild].info_color = int(value, 16)

    async def set_reply_embeds(self, guild: int, value: bool):
        await self.conn.execute(
            "UPDATE guild_settings SET reply_embeds=? WHERE Guild=?",
            (1 if value else 0, guild),
        )
        await self.conn.commit()
        self.guild_settings[guild].reply_embeds = value

    async def set_prefix(self, guild: int, prefix: str):
        await self.conn.execute(
            f"UPDATE guild_settings SET Prefix=? WHERE Guild=?", (prefix, guild)
        )
        await self.conn.commit()
        self.prefixes[guild] = prefix

    async def get_permissions(self, guild: int):
        if guild not in self.perm_chains:
            await self.conn.execute(
                "INSERT INTO permissions (guild) values (?)", (guild,)
            )
            await self.conn.commit()
            self.perm_chains[guild] = ["asm enable"]
        return [s for s in self.perm_chains[guild]]

    async def set_permissions(self, guild: int, perms: List[str]):
        self.perm_chains[guild] = [s for s in perms]
        await self.conn.execute(
            "UPDATE permissions SET permissions=? WHERE guild=?",
            (";".join(perms), guild),
        )

    async def add_permission(self, guild: int, perm: str):
        self.logger.info(f"db:adding permission {guild}:{perm}")
        self.perm_chains[guild].append(perm)
        await self.conn.execute(
            "UPDATE permissions SET permissions=? WHERE guild=?",
            (";".join(self.perm_chains[guild]), guild),
        )
        await self.conn.commit()

    async def remove_permission(self, guild: int, perm: int):
        del self.perm_chains[guild][perm]
        await self.conn.execute(
            "UPDATE permissions SET permissions=? WHERE guild=?",
            (";".join(self.perm_chains[guild]), guild),
        )
        await self.conn.commit()

    async def clear_permissions(self, guild: int):
        self.perm_chains[guild] = ["asm enable"]
        await self.conn.execute(
            "UPDATE permissions SET permissions=? WHERE guild=?",
            (";".join(self.perm_chains[guild]), guild),
        )
        await self.conn.commit()

    # endregion
