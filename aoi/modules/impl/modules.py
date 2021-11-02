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
import importlib
import os
import sys
import typing

import tanjun

from aoi import AoiContextMixin
from aoi.bot.injected import EmbedCreator


def _get_module_list() -> list[str]:
    return [file.removesuffix(".py") for file in os.listdir("aoi/modules/impl") if not file.startswith("_")]


async def list_modules(ctx: AoiContextMixin, _embed: EmbedCreator):
    await ctx.get_builder().as_info().with_title("Module List").with_description("\n".join(_get_module_list())).send()


async def reload_module(ctx: AoiContextMixin, module: str, _embed: EmbedCreator):
    if (module := module.lower()) not in _get_module_list():
        await ctx.get_builder().as_error().with_description("Invalid module").send()
        return
    try:
        importlib.reload(sys.modules[f"aoi.modules.impl.{module}"])
    except Exception as e:
        await ctx.get_builder().as_error().with_description(
            "An error occurred while reloading the module. `importlib` raised {e}"
        ).send()
        raise e
    try:
        typing.cast(tanjun.Client, ctx.client).reload_modules(f"aoi/modules/slash_commands/{module}.py")
    except ValueError:
        pass
    try:
        typing.cast(tanjun.Client, ctx.client).reload_modules(f"aoi/modules/message_commands/{module}.py")
    except ValueError:
        pass
    await ctx.get_builder().as_ok().with_description(f"Module {module} reloaded").send()
