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
import asyncio
import logging
import os
from pathlib import Path

import dotenv

from aoi.bot import injected
from aoi.bot.injected import ColorService
from aoi.bot.logging import LoggingHandler

if os.getenv("CUSTOM_LOGGER", ""):
    logging.setLoggerClass(LoggingHandler)

import hikari  # noqa E402
import tanjun  # noqa E402

from aoi.bot import AoiDatabase, HelpClient  # noqa 402

dotenv.load_dotenv()

assert (token := os.getenv("TOKEN"))
aoi = hikari.GatewayBot(token, intents=hikari.Intents.ALL)
client = tanjun.Client.from_gateway_bot(
    aoi, declare_global_commands=int(os.getenv("GUILD", 0)) or True
).load_modules(
    *Path("aoi/modules/message_commands").glob("**/*.py"),
    *Path("aoi/modules/slash_commands").glob("**/*.py"),
)
aoi_database = AoiDatabase(aoi)
help_client = HelpClient()

@aoi.listen(hikari.StartedEvent)
async def on_ready(_: hikari.StartedEvent):
    await aoi_database.load()


async def get_prefix(ctx: tanjun.abc.MessageContext):
    if ctx.guild_id and ctx.guild_id not in aoi_database.prefixes:
        asyncio.create_task(aoi_database.guild_setting(ctx.guild_id))
    return [
        aoi_database.prefixes.get(ctx.guild_id, ","),
        f"<@{aoi.get_me().id}>",
        f"<@!{aoi.get_me().id}>",
    ]


(
    client.set_type_dependency(
        injected.EmbedCreator, injected.EmbedCreator(aoi_database)
    )
    .set_type_dependency(AoiDatabase, aoi_database)
    .set_type_dependency(ColorService, ColorService())
    .set_type_dependency(HelpClient, help_client)
    .set_prefix_getter(get_prefix)
)

print(help_client.descriptions)

aoi.run()
