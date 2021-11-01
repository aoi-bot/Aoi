"""
Portions Copyright 2021 Yat-o

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
from typing import Optional

import aoi.modules.impl.information as impl
from aoi.bot import with_description
import tanjun
import hikari

component = tanjun.Component(name="information")


@component.with_command
@tanjun.with_greedy_argument("member", converters=(tanjun.to_member,), default=None)
@with_description("Show a user's avatar")
@tanjun.with_parser
@tanjun.as_message_command("avatar", "av")
async def avatar(ctx: tanjun.abc.MessageContext, member: Optional[hikari.Member]):
    await impl.avatar(ctx, member)


@component.with_command
@tanjun.with_argument("role", converters=(tanjun.to_role,), default=None)
@with_description("Reveal some info about a role")
@tanjun.with_parser
@tanjun.as_message_command("roleinfo")
async def roleinfo(ctx: tanjun.abc.MessageContext, role: hikari.Role):
    await impl.roleinfo(ctx, role)


@component.with_command
@tanjun.with_argument("user", converters=(tanjun.to_member,), default=None)
@with_description("Reveal some info about a user")
@tanjun.with_parser
@tanjun.as_message_command("userinfo", "uinfo")
async def userinfo(ctx: tanjun.abc.MessageContext, member: Optional[hikari.Member]):
    await impl.userinfo(ctx, member)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
