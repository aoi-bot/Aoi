"""
Portions Copyright 2021 Yat-o

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
from typing import Optional

import hikari

import aoi.modules.impl.channels as impl
from aoi import with_description, to_text_channel, AoiMessageContext

import tanjun

component = tanjun.Component(name="channels")


@component.with_command
@tanjun.with_author_permission_check(hikari.Permissions.MANAGE_CHANNELS)
@tanjun.with_own_permission_check(hikari.Permissions.MANAGE_CHANNELS)
@tanjun.with_greedy_argument("channel", converters=(to_text_channel,), default=None)
@with_description("Mark or unmark a channels NSFW flag")
@tanjun.with_parser
@tanjun.as_message_command("nsfw")
async def nsfw(ctx: AoiMessageContext, channel: hikari.GuildTextChannel):
    await impl.nsfw(ctx, channel)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
