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
import tanjun

import aoi.modules.impl.utility as impl
from aoi.bot import injected

component = tanjun.Component(name="utility")


@component.with_command
@tanjun.with_argument("base1", converters=(str,))
@tanjun.with_argument("base2", converters=(str,))
@tanjun.with_argument("value", converters=(str,))
@tanjun.with_parser
@tanjun.as_message_command("baseconvert", "bconv")
async def baseconvert(
    ctx: tanjun.abc.MessageContext,
    base1: str,
    base2: str,
    value: str,
    _embed: injected.EmbedCreator = tanjun.injected(type=injected.EmbedCreator),
):
    await impl.baseconvert(ctx, base1, base2, value, _embed)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
