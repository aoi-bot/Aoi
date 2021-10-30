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
from pathlib import Path

import hikari
import tanjun
from aoi.bot import HelpClient

class TestDescriptionChecks:
    def test_help_description(self):
        aoi = hikari.GatewayBot("", intents=hikari.Intents.ALL)
        client = tanjun.Client.from_gateway_bot(aoi).load_modules(
            *Path("aoi/modules/message_commands").glob("**/*.py"),
            *Path("aoi/modules/slash_commands").glob("**/*.py"),
        )
        help_client = HelpClient()
        for command in client.iter_message_commands():
            assert command in help_client.descriptions
