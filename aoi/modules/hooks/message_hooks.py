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
import logging
from datetime import datetime

import tanjun

from aoi.bot.injected import EmbedCreator

component = tanjun.Component(name="message_hooks")
hooks = tanjun.MessageHooks()


@hooks.with_on_parser_error
async def on_parser_error(ctx: tanjun.abc.MessageContext, error: tanjun.errors.ParserError) -> None:
    embed_creator: EmbedCreator = ctx.client.metadata["_embed"]
    if isinstance(error, tanjun.errors.ConversionError):
        await ctx.respond(
            embed=await embed_creator.error_embed(
                ctx,
                title="Could not convert argument",
                description=f"Argument `{error.args[1]}` could not be converted. See "
                f"{ctx.triggering_prefix}help {ctx.triggering_name}.",
            )
        )
    if isinstance(error, tanjun.errors.TooManyArgumentsError):
        await ctx.respond(
            embed=await embed_creator.error_embed(
                ctx,
                title="Too many arguments",
                description=f"Too many arguments were passed. See "
                f"{ctx.triggering_prefix}help {ctx.triggering_name}.",
            )
        )
    if isinstance(error, tanjun.errors.NotEnoughArgumentsError):
        await ctx.respond(
            embed=await embed_creator.error_embed(
                ctx,
                title="Some parameters unfilled",
                description=f"Some parameters were unfilled. See "
                f"{ctx.triggering_prefix}help {ctx.triggering_name}.",
            )
        )


@hooks.with_post_execution
async def post_exec(ctx: tanjun.abc.Context):
    logger = logging.getLogger("cmd")
    executed = datetime.now(tz=ctx.created_at.tzinfo) - ctx.created_at
    executed_str = f"{executed.total_seconds():>7.3f}s"
    message = (
        f"{ctx.triggering_name[:20]:>15} executed in {executed_str} from "
        f"{ctx.get_guild().name[:20]:>20} ({ctx.guild_id}) | "
        f"{ctx.get_channel().name[:10]:>10} ({ctx.channel_id})"
    )
    logger.info(message)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())
    client.set_hooks(hooks)


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
