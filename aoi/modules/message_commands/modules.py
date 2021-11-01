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

from aoi.bot.injected import EmbedCreator
from aoi.modules.impl import modules as impl

component = tanjun.Component(name="modules")


@component.with_command
@tanjun.as_message_command_group("modules")
async def modules(ctx: tanjun.abc.MessageContext):
    await impl.list_modules(ctx)


@modules.with_command
@tanjun.with_owner_check
@tanjun.as_message_command("list")
async def modules_list(
    ctx: tanjun.abc.MessageContext,
    _embed: EmbedCreator = tanjun.injected(type=EmbedCreator),
):
    await impl.list_modules(ctx, _embed)


@modules.with_command
@tanjun.with_owner_check
@tanjun.with_greedy_argument("module")
@tanjun.with_parser
@tanjun.as_message_command("reload")
async def modules_reload(
    ctx: tanjun.abc.MessageContext,
    module: str,
    _embed: EmbedCreator = tanjun.injected(type=EmbedCreator),
):
    await impl.reload_module(ctx, module, _embed)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
