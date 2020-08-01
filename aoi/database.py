import logging
from dataclasses import dataclass
from typing import Dict, Optional

import aiosqlite
from aiosqlite import Connection


@dataclass
class _GuildSetting:
    ok_color: int
    error_color: int
    info_color: int



class AoiDatabase:
    def __init__(self):
        self.db: Optional[Connection] = None
        self.guild_settings: Dict[int, _GuildSetting] = {}

    async def load(self):
        self.db = await aiosqlite.connect("database.db")
        logging.info("[DB] Loading database into memory")
        cursor = await self.db.execute("SELECT * from guild_settings")
        rows = await cursor.fetchall()
        await cursor.close()
        for r in rows:
            self.guild_settings[r[0]] = _GuildSetting(*(int(color, 16) for color in r[1:]))

    async def close(self):
        await self.db.close()

    async def guild_setting(self, guild: int) -> _GuildSetting:
        if guild not in self.guild_settings:
            await self.db.execute("INSERT INTO guild_settings (Guild) values (?)", (guild,))
            await self.db.commit()
            self.guild_settings[guild] = _GuildSetting(
                ok_color=0x00aa00,
                error_color=0xaa0000,
                info_color=0x0000aa
            )
        return self.guild_settings[guild]

    async def set_ok_color(self, guild: int, value: str):
        await self.db.execute(f"UPDATE guild_settings SET OkColor=? WHERE Guild=?", (value, guild))
        await self.db.commit()
        self.guild_settings[guild].ok_color = int(value, 16)

    async def set_error_color(self, guild: int, value: str):
        await self.db.execute(f"UPDATE guild_settings SET ErrorColor=? WHERE Guild=?", (value, guild))
        await self.db.commit()
        self.guild_settings[guild].ok_color = int(value, 16)

    async def set_info_color(self, guild: int, value: str):
        await self.db.execute(f"UPDATE guild_settings SET InfoColor=? WHERE Guild=?", (value, guild))
        await self.db.commit()
        self.guild_settings[guild].ok_color = int(value, 16)
