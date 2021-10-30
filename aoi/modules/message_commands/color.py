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
from collections.abc import Sequence

import tanjun

import aoi.modules.impl.color as impl
from aoi.libs.converters import FuzzyAoiColor

component = tanjun.Component(name="color")


@component.with_command
@tanjun.with_multi_argument("colors", converters=(FuzzyAoiColor.convert,))
@tanjun.with_parser
@tanjun.as_message_command("colors", "color")
async def color_palette(
    ctx: tanjun.abc.MessageContext, color_list: Sequence[FuzzyAoiColor]
):
    await impl.color_palette(ctx, color_list)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
