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
import typing

import hikari
import tanjun

if typing.TYPE_CHECKING:
    from ..contexts import AoiContextMixin

from ..database import AoiDatabase


class EmbedBuilder:
    def __init__(
        self,
        ctx: "AoiContextMixin",
        title: typing.Any = None,
        description: typing.Any = None,
        url: typing.Optional[str] = None,
        color: typing.Optional[hikari.Colorish] = None,
    ):
        self._title = title
        self._description = description
        self._url = url
        self._ctx = ctx
        self._slash: bool = isinstance(ctx, tanjun.abc.SlashContext)
        self._db: AoiDatabase = ctx.client.metadata["database"]
        self._fields: list[tuple[str, str, bool]] = []
        self._thumbnail: typing.Optional[hikari.Resourceish] = None
        self._image: typing.Optional[hikari.Resourceish] = None
        self._footer: typing.Optional[tuple[str, typing.Optional[hikari.Resourceish]]] = None
        self._author: typing.Optional[
            tuple[typing.Optional[str], typing.Optional[str], typing.Optional[hikari.Resourceish]]
        ] = None
        self._color: typing.Union[typing.Literal[0, 1, 2], hikari.Color] = hikari.Color.of(color) if color else 1

    OK = 0
    INFO = 1
    ERROR = 2

    def with_url(self, url: str) -> "EmbedBuilder":
        self._url = url
        return self

    def with_title(self, title: str) -> "EmbedBuilder":
        self._title = title
        return self

    def with_description(self, description: str) -> "EmbedBuilder":
        self._description = description
        return self

    def add_field(self, name: str, value: str, /, *, inline: bool = False) -> "EmbedBuilder":
        self._fields.append((name, value, inline))
        return self

    def with_thumbnail(self, image: hikari.Resourceish) -> "EmbedBuilder":
        self._thumbnail = image
        return self

    def with_image(self, image: hikari.Resourceish) -> "EmbedBuilder":
        self._image = image
        return self

    def with_footer(self, text: str, *, icon: hikari.Resourceish = None) -> "EmbedBuilder":
        self._footer = text, icon
        return self

    def with_author(self, *, name: str = None, url: str = None, icon: hikari.Resourceish = None) -> "EmbedBuilder":
        self._author = name, url, icon
        return self

    def as_ok(self) -> "EmbedBuilder":
        self._color = self.OK
        return self

    def as_info(self) -> "EmbedBuilder":
        self._color = self.INFO
        return self

    def as_error(self) -> "EmbedBuilder":
        self._color = self.ERROR
        return self

    def as_custom(self, color: hikari.Color) -> "EmbedBuilder":
        self._color = color
        return self

    async def build(self) -> hikari.Embed:
        if isinstance(self._color, hikari.Color):
            color = self._color
        else:
            setting = await self._db.guild_setting(self._ctx.guild_id)
            color = hikari.Color.of([setting.ok_color, setting.info_color, setting.error_color][self._color])

        embed = hikari.Embed(color=color, title=self._title, description=self._description, url=self._url)
        for field in self._fields:
            embed.add_field(field[0], field[1], inline=field[2])
        if self._thumbnail:
            embed.set_thumbnail(self._thumbnail)
        if self._image:
            embed.set_image(self._image)
        if self._author:
            embed.set_author(name=self._author[0], url=self._author[1], icon=self._author[2])
        if self._footer:
            embed.set_footer(self._footer[0], icon=self._footer[1])
        return embed

    @typing.overload
    async def build_no_embed(self, return_image: typing.Literal[True]) -> tuple[str, hikari.Resourceish]:
        ...

    @typing.overload
    async def build_no_embed(self) -> str:
        ...

    async def build_no_embed(self, *, return_image: bool = False) -> typing.Union[tuple[str, hikari.Resourceish], str]:
        builder = ""
        if self._title:
            builder += f"**[{self._title}]({self._url})**\n" if self._url else f"**{self._title}**\n"
        if self._author:
            builder += f"{self._author}\n"
        if self._description:
            builder += f"{self._description}\n"
        if self._fields:
            builder += "\n"
        for field in self._fields:
            builder += f"**{field[0]}**\n{field[1]}\n\n"
        if self._footer:
            builder += self._footer
        return (builder, self._image) if return_image else builder

    async def send(self):
        await self._ctx.respond(await self.build())
