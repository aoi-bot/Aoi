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
import typing

import hikari
import tanjun

from aoi import HelpClient

component = tanjun.Component(name="events")
tanjun_client: typing.Optional[tanjun.Client] = None


@component.with_listener(hikari.StartedEvent)
async def bot_started(event: hikari.StartedEvent, help_client: HelpClient = tanjun.injected(type=HelpClient)):
    logger = logging.getLogger("check.commands")
    for command in tanjun_client.iter_message_commands():
        if not help_client.get_help_for(command) and help_client.is_visible(command):
            logger.warning(
                f"Command {command.component.name}.{typing.cast(list[str], command.names)[0]} has no help description"
            )


@tanjun.as_loader
def load(client: tanjun.Client):
    global tanjun_client
    tanjun_client = client
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
