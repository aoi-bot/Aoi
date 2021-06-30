from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict

import aiohttp

if TYPE_CHECKING:
    from bot.aoi.aoi_bot import AoiBot


class AoiRoute:
    def __init__(self, secret: str, connection, port: int, path: str, replacements=()):
        for replacement in replacements:
            path = path.replace("?", str(replacement), 1)
        self.path = f"http://127.0.0.1:{port}/{path}"
        self.__con = connection
        self.secret = secret
        self.headers = {
            "Authorization": self.secret
        }

    async def post(self, json=None) -> Dict:
        async with self.__con.post(self.path, json=json, headers=self.headers) as resp:
            return await resp.json()

    async def patch(self, json=None) -> Dict:
        async with self.__con.patch(self.path, json=json, headers=self.headers) as resp:
            return await resp.json()

    async def put(self, json=None) -> Dict:
        async with self.__con.put(self.path, json=json, headers=self.headers) as resp:
            return await resp.json()

    async def delete(self, json=None) -> Dict:
        async with self.__con.delete(self.path, json=json, headers=self.headers) as resp:
            return await resp.json()

    async def get(self) -> Dict:
        async with self.__con.get(self.path, headers=self.headers) as resp:
            return await resp.json()


class AoiRouteManager:
    def __init__(self, bot: AoiBot):
        self.bot = bot
        self.secret = bot.secret
        self.__con = aiohttp.ClientSession()

    @property
    def port(self) -> int:
        return self.bot.config.get("api.port")

    def r(self, path, replacements=()) -> AoiRoute:
        return AoiRoute(self.secret, self.__con, self.port, path, replacements)
