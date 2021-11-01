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

import aoi.modules.impl.fun as impl
from aoi import AoiMessageContext
from aoi.bot import injected

component = tanjun.Component(name="fun")


@component.with_command
@tanjun.with_argument("height", converters=(int,), default=10)
@tanjun.with_argument("width", converters=(int,), default=10)
@tanjun.with_argument("bombs", converters=(int,), default=10)
@tanjun.with_option("raw", "--raw", "-r", converters=(bool,), default=False, empty_value=True)
@tanjun.with_option(
    "no_spoiler",
    "--no-spoiler",
    "-n",
    converters=(bool,),
    default=True,
    empty_value=False,
)
@tanjun.with_parser
@tanjun.as_message_command("minesweeper", "mines")
async def minesweeper(
    ctx: AoiMessageContext,
    height: int,
    width: int,
    bombs: int,
    raw: bool,
    no_spoiler: bool,
    _embed: injected.EmbedCreator = tanjun.injected(type=injected.EmbedCreator),
):
    await impl.minesweeper(ctx, height, width, bombs, raw, no_spoiler, _embed)


@component.with_command
@tanjun.with_greedy_argument("member", converters=(tanjun.to_member,), default=None)
@tanjun.with_parser
@tanjun.as_message_command("simp")
async def simp(ctx: AoiMessageContext, member: typing.Optional[hikari.Member]):
    await impl.simp(ctx, member)


# TODO add ttt again


@component.with_command
@tanjun.as_message_command("animequote")
# TODO this needs a cooldown once tanjun implements - dpy was 1/5s/user
async def anime_quote(
    ctx: AoiMessageContext,
    _embed: injected.EmbedCreator = tanjun.injected(type=injected.EmbedCreator),
):
    await impl.anime_quote(ctx, _embed)


@component.with_command
@tanjun.as_message_command("waifu")
async def waifu(ctx: AoiMessageContext):
    await impl.waifu(ctx)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
