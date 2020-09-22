import asyncio
import io
import json
from types import coroutine
from typing import List, Tuple, Union, Any, Callable

import discord
import disputils
from discord.ext import commands


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

    async def done_ping(self):
        return await self.send(f"{self.author.mention}, done! {self.message.jump_url}")

    async def send_info(self, message: str, *, user: discord.abc.User = None,
                        title: str = None, trash: bool = False):
        if not user:
            user = self.author
        msg = await self.send(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(self.INFO)
        ))
        if trash:
            await self.trash_reaction(msg)
        else:
            return msg

    async def send_ok(self, message: str, *, user: discord.abc.User = None,
                      title: str = None, trash: bool = False):
        if not user:
            user = self.author
        msg = await self.send(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(self.OK)
        ))
        if trash:
            await self.trash_reaction(msg)
        else:
            return msg

    async def send_error(self, message: str, *, user: discord.abc.User = None,
                         title: str = None, trash: bool = False):
        if not user:
            user = self.author
        msg = await self.send(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(self.ERROR)
        ))
        if trash:
            await self.trash_reaction(msg)
        else:
            return msg

    async def edit_message(self, message: discord.Message, content: str, *, user: discord.abc.User = None,
                           title: str = None, color: int = 0):
        if not user:
            user = self.author
        await message.edit(embed=discord.Embed(
            title=title,
            description=f"{_wrap_user(user) if user else ''}{message}",
            colour=await self.get_color(color)
        ))
        return message

    async def get_color(self, typ: int):
        if typ == 0:
            return discord.Color((await self.bot.db.guild_setting(self.guild.id)).info_color)
        if typ == 1:
            return discord.Color((await self.bot.db.guild_setting(self.guild.id)).error_color)
        if typ == 2:
            return discord.Color((await self.bot.db.guild_setting(self.guild.id)).ok_color)
        raise ValueError

    # noinspection PyDefaultArgument
    async def embed(self, *,
                    author: str = None,
                    description: str = None,
                    title: str = None,
                    title_url: str = None,
                    typ: int = INFO,
                    fields: List[Tuple[str, str]] = None,
                    thumbnail: str = None,
                    clr: discord.Colour = None,
                    image: Union[str, io.BufferedIOBase] = None,
                    footer: str = None,
                    not_inline: List[int] = [],
                    trash_reaction: bool = False):
        if typ and clr:
            raise ValueError("typ and clr can not be both defined")
        embed = discord.Embed(
            title=title,
            description=description,
            colour=(await self.get_color(typ) if not clr else clr),
            title_url=title_url
        )
        if author:
            embed.set_author(name=author)
        if image:
            if isinstance(image, str):
                embed.set_image(url=image)
                f = None
            else:
                image.seek(0)
                f = discord.File(image, filename="image.png")
                embed.set_image(url="attachment://image.png")
        else:
            f = None
        if footer:
            embed.set_footer(text=footer)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        for n, r in enumerate(fields or []):
            embed.add_field(name=r[0], value=r[1] or "None", inline=n not in not_inline)
        msg = await self.send(embed=embed, file=f)
        if trash_reaction:
            await self.trash_reaction(msg)

    @staticmethod
    def group_list(lst: List[Any], n: int) -> List[List[Any]]:
        """
        Splits a list into sub-lists of n
        :param lst: the list
        :param n: the subgroup size
        :return: The list of lists
        """
        return [lst[i * n:(i + 1) * n] for i in range((len(lst) + n - 1) // n)]

    async def pages(self, lst: List[Any], n: int,
                    title: str, *, fmt: str = "%s",
                    thumbnails: List[str] = None, sep: str = "\n", color=None) \
            -> List[discord.Embed]:
        # noinspection GrazieInspection
        """
            Paginates a list into embeds to use with :class:disputils.BotEmbedPaginator

            :param lst: the list to paginate
            :param n: the number of elements per page
            :param title: the title of the embed
            :param fmt: a % string used to format the resulting page
            :param sep: the string to join the list elements with
            :param thumbnails: thumbnail
            :param color: color
            :return: a list of embeds
            """
        l: List[List[str]] = self.group_list([str(i) for i in lst], n)
        pgs = [sep.join(page) for page in l]
        if not thumbnails:
            return [
                discord.Embed(
                    title=f"{title} - {i + 1}/{len(pgs)}",
                    description=fmt % pg,
                    color=color or await self.get_color(self.OK),
                ) for i, pg in enumerate(pgs)
            ]
        else:
            return [
                discord.Embed(
                    title=f"{title} - {i + 1}/{len(pgs)}",
                    description=fmt % pg,
                    color=color or await self.get_color(self.OK),
                ).set_thumbnail(url=thumbnails[i]) for i, pg in enumerate(pgs)
            ]

    @staticmethod
    def numbered(lst: List[Any]) -> List[str]:
        """

        Returns a numbered version of a list
        """
        return [f"**{i}.** {a}" for i, a in enumerate(lst)]

    async def paginate(self, lst: List[Any], n: int,
                       title: str, *, fmt: str = "%s", sep: str = "\n",
                       numbered: bool = False, thumbnails: List[str] = None):
        if numbered:
            lst = self.numbered(lst)
        paginator = disputils.BotEmbedPaginator(self,
                                                await self.pages(lst, n, title,
                                                                 fmt=fmt, sep=sep,
                                                                 thumbnails=thumbnails,
                                                                 color=await self.get_color(self.INFO)))
        await paginator.run()

    async def page_predefined(self, *embeds: List[discord.Embed]):
        paginator = disputils.BotEmbedPaginator(self, embeds)
        await paginator.run()

    async def input(self, typ: type, cancel_str: str = "cancel", ch: Callable = None, err=None, check_author=True,
                    return_author=False, del_error=60, del_response=False, timeout=60.0):
        def check(m):
            return ((m.author == self.author and m.channel == self.channel) or not check_author) and not m.author.bot

        while True:
            try:
                inp: discord.Message = await self.bot.wait_for('message', check=check, timeout=timeout)
                if del_response:
                    await inp.delete()
                if inp.content.lower() == cancel_str.lower():
                    return (None, None) if return_author else None
                res = typ(inp.content.lower())
                if ch:
                    if not ch(res): raise ValueError
                return (res, inp.author) if return_author else res
            except ValueError:
                await self.send(err or "That's not a valid response, try again" +
                                ("" if not cancel_str else f" or type `{cancel_str}` to quit"), delete_after=del_error)
                continue
            except asyncio.TimeoutError:
                await self.send("You took too long to respond ): Try to start over", delete_after=del_error)
                return (None, None) if return_author else None

    async def send_json(self, msg: str):
        msg = self.bot.placeholders.replace(self, msg)
        try:
            msg = json.loads(msg)
        except json.JSONDecodeError:
            msg = {
                "plainText": msg
            }
        if isinstance(msg, str):
            msg = {
                "plainText": msg
            }
        if "plainText" in msg:
            content = msg.pop("plainText")
        else:
            content = None
        if len(msg.keys()) < 2:  # no embed here:
            embed = None
        else:
            embed = msg
        if embed:
            _ = embed.pop("thumbnail", None)
        await self.send(
            content=content,
            embed=discord.Embed.from_dict(embed) if embed else None
        )
