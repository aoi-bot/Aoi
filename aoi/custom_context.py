from typing import List, Tuple, Union

import discord
from discord.ext import commands


class AoiContext(commands.Context):
    INFO = 0
    ERROR = 1
    OK = 2

    async def send_info(self, message: str, *, user: discord.abc.User = None, title: str = None):
        await self.send(embed=discord.Embed(
            title=title,
            description=f"{user if user else ''}{message}",
            colour=await self.get_color(self.INFO)
        ))

    async def send_ok(self, message: str, *, user: discord.abc.User = None, title: str = None):
        await self.send(embed=discord.Embed(
            title=title,
            description=f"{user if user else ''}{message}",
            colour=await self.get_color(self.OK)
        ))

    async def send_error(self, message: str, *, user: discord.abc.User = None, title: str = None):
        await self.send(embed=discord.Embed(
            title=title,
            description=f"{user if user else ''}{message}",
            colour=await self.get_color(self.ERROR)
        ))

    async def get_color(self, typ: int):
        if typ == 0:
            return discord.Color((await self.bot.db.guild_setting(self.guild.id)).info_color)
        if typ == 1:
            return discord.Color((await self.bot.db.guild_setting(self.guild.id)).error_color)
        if typ == 2:
            return discord.Color((await self.bot.db.guild_setting(self.guild.id)).ok_color)
        raise ValueError

    async def embed(self, *,
                    description: str = None,
                    title: str = None,
                    typ: int = INFO,
                    fields: List[Tuple[str, str]] = None,
                    thumbnail: str = None,
                    clr: discord.Colour = None):
        if typ and clr:
            raise ValueError("typ and clr can not be both defined")
        embed = discord.Embed(
            title=title,
            description=description,
            colour=(await self.get_color(typ) if not clr else clr)
        )
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        for r in fields:
            embed.add_field(name=r[0], value=r[1])
        await self.send(embed=embed)
