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
from aoi import AoiMessageContext
from aoi.bot import with_description, AoiDatabase
from aoi.bot.injected import EmbedCreator, ColorService
from aoi.libs.converters import FuzzyAoiColor, AoiColor

component = tanjun.Component(name="color")


@component.with_command
@tanjun.with_multi_argument("colors", converters=(FuzzyAoiColor.convert,))
@tanjun.with_parser
@with_description("Show a color palette made up of supplied colors")
@tanjun.as_message_command("colors", "color")
async def color_palette(ctx: AoiMessageContext, color_list: Sequence[FuzzyAoiColor]):
    await impl.color_palette(ctx, color_list)


@component.with_command
@tanjun.with_argument("number_of_colors", converters=(int,), default=4)
@tanjun.with_option("sort_by", "--sort", converters=(str,), default="hue")
@with_description("Show a random color palette")
@tanjun.with_parser
@tanjun.as_message_command("randomcolors", "ranclr")
async def random_colors(
    ctx: AoiMessageContext,
    number_of_colors: int,
    sort_by: str,
    _embed: EmbedCreator = tanjun.injected(type=EmbedCreator),
    _database: AoiDatabase = tanjun.injected(type=AoiDatabase),
):
    await impl.random_colors(ctx, number_of_colors, sort_by, _embed, _database)


@component.with_command
@tanjun.with_argument("number_of_colors", converters=(int,), default=4)
@tanjun.with_argument("color2", converters=(AoiColor.convert,))
@tanjun.with_argument("color1", converters=(AoiColor.convert,))
@tanjun.with_option("rgb", "--rgb", converters=(bool,), default=False, empty_value=True)
@with_description("Make a gradient between colors")
@tanjun.with_parser
@tanjun.as_message_command("gradient")
async def gradient(
    ctx: AoiMessageContext,
    color1: AoiColor,
    color2: AoiColor,
    number_of_colors: int,
    rgb: bool,
    _database: AoiDatabase = tanjun.injected(type=AoiDatabase),
    _colors: ColorService = tanjun.injected(type=ColorService),
):
    await impl.gradient(ctx, color1, color2, number_of_colors, rgb, _database, _colors)


# TODO add duotone
# TODO add adaptive
# TODO add histogram


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
