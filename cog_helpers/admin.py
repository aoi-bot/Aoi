"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from typing import List, Union, Final, Optional

import aiohttp

import discord
from aoi import AoiMessageModel


class _Missing:
    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return 'Missing'

    def __len__(self) -> int:
        return 0

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__)


Missing: Final = _Missing()


class AdminService:
    def __init__(self, port):
        self.port = port

    async def get_self_roles(self, guild: discord.Guild) -> List[int]:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"http://127.0.0.1:{self.port}/self-roles/{guild.id}") as resp:
                return (await resp.json())["results"]

    async def add_self_role(self, guild: discord.Guild, role: discord.Role) -> bool:
        async with aiohttp.ClientSession() as sess:
            async with sess.put(
                    f"http://127.0.0.1:{self.port}/self-roles/{guild.id}",
                    json={'role': role.id}
            ) as resp:
                return (await resp.json())["results"]

    async def remove_self_role(self, guild: discord.Guild, role: Union[discord.Role, int]) -> None:
        if isinstance(role, discord.Role):
            role = role.id
        async with aiohttp.ClientSession() as sess:
            async with sess.delete(
                    f"http://127.0.0.1:{self.port}/self-roles/{guild.id}",
                    json={'role': role}
            ) as resp:
                return (await resp.json())["results"]

    async def get_welcome_message(self, guild: int) -> AoiMessageModel:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"http://127.0.0.1:{self.port}/messages/greet/{guild}") as resp:
                return AoiMessageModel(*(await resp.json())["results"])

    async def get_goodbye_message(self, guild: int) -> AoiMessageModel:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"http://127.0.0.1:{self.port}/messages/leave/{guild}") as resp:
                return AoiMessageModel(*(await resp.json())["results"])

    async def set_welcome_message(self, guild: int, *, channel: Optional[discord.TextChannel] = Missing,
                                  delete_after: int = None, message: str = None):
        async with aiohttp.ClientSession() as sess:
            await sess.patch(f"http://127.0.0.1:{self.port}/messages/greet/{guild}",
                             json={
                                 "message": message,
                                 "channel": channel.id if channel else (0 if channel != Missing else None),
                                 "delete": delete_after
                             })

    async def set_goodbye_message(self, guild: int, *, channel: Optional[discord.TextChannel] = Missing,
                                  delete_after: int = None, message: str = None):
        async with aiohttp.ClientSession() as sess:
            await sess.patch(f"http://127.0.0.1:{self.port}/messages/leave/{guild}",
                             json={
                                 "message": message,
                                 "channel": channel.id if channel else (0 if channel != Missing else None),
                                 "delete": delete_after
                             })
