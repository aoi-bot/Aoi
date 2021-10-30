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

import modules.impl.utility as impl
from bot import injected

component = tanjun.Component(name="utility-slash")
utility_group = component.with_slash_command(
    tanjun.SlashCommandGroup("utility", "Various utility commands")
)


@utility_group.with_command
@tanjun.with_str_slash_option(
    "base2",
    "The base to convert to",
    choices={x: x.lower()[:3] for x in ["Hexadecimal", "Decimal", "Binary", "Octal"]},
)
@tanjun.with_str_slash_option(
    "base1",
    "The base to convert from",
    choices={x: x.lower()[:3] for x in ["Hexadecimal", "Decimal", "Binary", "Octal"]},
)
@tanjun.with_str_slash_option("value", "The value to convert")
@tanjun.as_slash_command("base-convert", "Convert a value between bases")
async def baseconvert(
    ctx: tanjun.abc.SlashContext,
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
