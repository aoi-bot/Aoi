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

import modules.impl.fun as impl
from bot import injected

component = tanjun.Component(name="fun-slash")
fun_group = component.with_slash_command(
    tanjun.SlashCommandGroup("fun", "Fun and games :D")
)


@fun_group.with_command
@tanjun.with_int_slash_option("height", "The height of the board", default=10)
@tanjun.with_int_slash_option("width", "The width of the board", default=10)
@tanjun.with_int_slash_option("bombs", "The number of bombs on the board", default=10)
@tanjun.with_str_slash_option(
    "raw",
    "Send the raw spoiler content?",
    choices={"Yes": "yes", "No": "no"},
    default="no",
)
@tanjun.with_str_slash_option(
    "spoilers", "Use spoilers?", choices={"Yes": "yes", "No": "no"}, default="yes"
)
@tanjun.as_slash_command("minesweeper", "Make a spoiler (or not) minesweeper game")
async def minesweeper(
    ctx: tanjun.abc.SlashContext,
    height: int,
    width: int,
    bombs: int,
    raw: str,
    spoilers: str,
    _embed: injected.EmbedCreator = tanjun.injected(type=injected.EmbedCreator),
):
    await impl.minesweeper(
        ctx, height, width, bombs, raw == "yes", spoilers == "yes", _embed
    )


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
