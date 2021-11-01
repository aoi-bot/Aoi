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

import aoi


class EmbedCreator:
    OK = 0
    INFO = 1
    ERROR = 2

    def __init__(self, db: aoi.bot.database.AoiDatabase, /):
        self._db = db

    async def send(
        self,
        ctx: typing.Union[tanjun.abc.SlashContext, tanjun.abc.MessageContext],
        typ: typing.Literal[0, 1, 2],
        content: str,
    ):
        if isinstance(ctx, tanjun.abc.SlashContext):
            if typ == 2:
                ctx.set_ephemeral_default(True)
            await ctx.respond(content)
        else:
            await ctx.respond(
                embed=await ([self.ok_embed, self.info_embed, self.error_embed][typ](ctx, description=content))
            )

    async def ok_embed(
        self,
        ctx: tanjun.abc.Context,
        /,
        *,
        title: typing.Any = None,
        description: typing.Any = None,
    ) -> hikari.Embed:
        assert title or description
        return hikari.Embed(
            title=title,
            description=description,
            colour=(await self._db.guild_setting(ctx.guild_id)).ok_color,
        )

    async def error_embed(
        self,
        ctx: tanjun.abc.Context,
        /,
        *,
        title: typing.Any = None,
        description: typing.Any = None,
    ) -> hikari.Embed:
        assert title or description
        return hikari.Embed(
            title=title,
            description=description,
            colour=(await self._db.guild_setting(ctx.guild_id)).error_color,
        )

    async def info_embed(
        self,
        ctx: tanjun.abc.Context,
        /,
        *,
        title: typing.Any = None,
        description: typing.Any = None,
    ) -> hikari.Embed:
        assert title or description
        return hikari.Embed(
            title=title,
            description=description,
            colour=(await self._db.guild_setting(ctx.guild_id)).info_color,
        )
