from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, List, TYPE_CHECKING
import aiosqlite
from aiosqlite import Connection

if TYPE_CHECKING:
    import aoi

@dataclass
class _GuildSetting:
    ok_color: int
    error_color: int
    info_color: int
    perm_errors: bool


class AoiDatabase:
    def __init__(self, bot: aoi.AoiBot):
        self.db: Optional[Connection] = None
        self.guild_settings: Dict[int, _GuildSetting] = {}
        self.prefixes: Dict[int, str] = {}
        self.perm_chains: Dict[int, List[str]] = {}
        self.bot = bot

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

    async def close(self):
        await self.db.close()

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
