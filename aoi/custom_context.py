import asyncio
import io
from types import coroutine
from typing import List, Tuple, Union

import discord
from discord.ext import commands
import disputils


def _wrap_user(user: discord.abc.User):
    return f"**{user}** "


class AoiContext(commands.Context):
    INFO = 0
    ERROR = 1
    OK = 2

    async def trash_reaction(self, message: discord.Message):
        if len(message.embeds) == 0:
            return

        def check(_reaction: discord.Reaction, _user: Union[discord.User, discord.Member]):
            return all([
                _user.id == self.author.id or _user.guild_permissions.manage_messages,
                _reaction.message.id == message.id,
                str(_reaction) == "🗑️"
            ])

        await message.add_reaction("🗑️")
        await asyncio.sleep(0.5)
        try:
            _, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message.clear_reactions()
        else:
            await message.delete()

    async def confirm(self, message: str, confirmed: str, denied: str):
        conf = disputils.BotConfirmation(self, color=await self.get_color(self.INFO))
        await conf.confirm(message)
        if conf.confirmed:
            await conf.update(text=confirmed, color=await self.get_color(self.OK))
        else:
            await conf.update(text=denied, color=await self.get_color(self.ERROR))
        return conf.confirmed

    async def confirm_coro(self, message: str, confirmed: str, denied: str, coro: coroutine):
        conf = disputils.BotConfirmation(self, color=await self.get_color(self.INFO))
        await conf.confirm(message)
        if conf.confirmed:
            await coro
            await conf.update(text=confirmed, color=await self.get_color(self.OK))
        else:
            await conf.update(text=denied, color=await self.get_color(self.ERROR))
        return conf.confirmed

    async def send_info(self, message: str, *, user: discord.abc.User = None,
                      title: str = None, trash: bool = True):
        if not user:
            user = self.author
        msg = await self.send(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(self.INFO)
        ))
        if trash:
            await self.trash_reaction(msg)

    async def send_ok(self, message: str, *, user: discord.abc.User = None,
                      title: str = None, trash: bool = True):
        if not user:
            user = self.author
        msg = await self.send(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(self.OK)
        ))
        if trash:
            await self.trash_reaction(msg)

    async def send_error(self, message: str, *, user: discord.abc.User = None,
                      title: str = None, trash: bool = True):
        if not user:
            user = self.author
        msg = await self.send(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(self.ERROR)
        ))
        if trash:
            await self.trash_reaction(msg)

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
                    clr: discord.Colour = None,
                    image: Union[str, io.BufferedIOBase] = None,
                    footer: str = None):
        if typ and clr:
            raise ValueError("typ and clr can not be both defined")
        embed = discord.Embed(
            title=title,
            description=description,
            colour=(await self.get_color(typ) if not clr else clr)
        )
        if isinstance(image, str):
            embed.set_image(url=image)
            f = None
        else:
            image.seek(0)
            f = discord.File(image, filename="image.png")
            embed.set_image(url="attachment://image.png")
        if footer:
            embed.set_footer(text=footer)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        for r in fields or []:
            embed.add_field(name=r[0], value=r[1])
        msg = await self.send(embed=embed, file=f)
        await self.trash_reaction(msg)
