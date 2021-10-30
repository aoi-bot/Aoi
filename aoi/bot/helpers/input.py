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
import asyncio
import typing
from collections.abc import Callable

import hikari
import tanjun

_T = typing.TypeVar("_T")


class InputHelper:
    def __init__(self, ctx: tanjun.abc.MessageContext):
        self._ctx = ctx
        self._bot = typing.cast(hikari.GatewayBot, ctx.shards)

    @typing.overload
    async def input(
        self,
        typ: typing.Type[_T],
        /,
        *,
        err_str: typing.Optional[str] = None,
        cancel_str: typing.Optional[str] = "cancel",
        ch: typing.Optional[Callable[[_T], bool]] = None,
        check_author: bool = True,
        return_author: bool = typing.Literal[False],
        # del_error: int = 60,
        del_response: int = False,
    ) -> _T:
        ...

    @typing.overload
    async def input(
        self,
        typ: typing.Type[_T],
        /,
        *,
        err_str: typing.Optional[str] = None,
        cancel_str: typing.Optional[str] = "cancel",
        ch: typing.Optional[Callable[[_T], bool]] = None,
        check_author: bool = True,
        return_author: bool = typing.Literal[True],
        # del_error: int = 60,
        del_response: int = False,
    ) -> tuple[_T, hikari.User]:
        ...

    async def input(
        self,
        typ: typing.Type[_T],
        /,
        *,
        err_str: typing.Optional[str] = None,
        cancel_str: typing.Optional[str] = "cancel",
        ch: typing.Optional[Callable[[_T], bool]] = None,
        check_author: bool = True,
        return_author: bool = False,
        # del_error: int = 60,
        del_response: int = False,
    ):
        def check(event: hikari.MessageCreateEvent):
            return (
                (
                    event.author_id == self._ctx.author.id
                    and event.channel_id == self._ctx.channel_id
                )
                or not check_author
            ) and not event.author.is_bot

        while True:
            try:
                inp: hikari.MessageCreateEvent = await self._bot.wait_for(
                    hikari.MessageCreateEvent, 60, check
                )
                if del_response:
                    try:
                        await inp.message.delete()
                    except hikari.ForbiddenError:
                        pass
                if inp.content.lower() == cancel_str.lower():
                    return (None, None) if return_author else None
                res = typ(inp.content.lower())
                if ch and not ch(res):
                    raise ValueError
                return (res, inp.author) if return_author else res
            except ValueError:
                await self._ctx.respond(
                    err_str
                    or "That's not a valid response, try again"
                    + ("" if not cancel_str else f" or type `{cancel_str}` to quit")
                )
            except asyncio.TimeoutError:
                await self._ctx.respond(
                    "You took too long to respond ): Try to start over"
                )
                return (None, None) if return_author else None
