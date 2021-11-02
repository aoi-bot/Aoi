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

import hikari
import tanjun

import aoi.modules.impl.information as impl
from aoi import AoiMessageContext, to_voice_channel, to_text_channel
from aoi.bot import with_description

component = tanjun.Component(name="information")


@component.with_command
@tanjun.with_greedy_argument("member", converters=(tanjun.to_member,), default=None)
@with_description("Show a user's avatar")
@tanjun.with_parser
@tanjun.as_message_command("avatar", "av")
async def avatar(ctx: AoiMessageContext, member: Optional[hikari.Member]):
    await impl.avatar(ctx, member)


@component.with_command
@tanjun.with_argument("role", converters=(tanjun.to_role,), default=None)
@with_description("Reveal some info about a role")
@tanjun.with_parser
@tanjun.as_message_command("roleinfo", "rinfo")
async def roleinfo(ctx: AoiMessageContext, role: hikari.Role):
    await impl.roleinfo(ctx, role)


@component.with_command
@tanjun.with_argument("user", converters=(tanjun.to_member,), default=None)
@with_description("Reveal some info about a user")
@tanjun.with_parser
@tanjun.as_message_command("userinfo", "uinfo")
async def userinfo(ctx: AoiMessageContext, member: Optional[hikari.Member]):
    await impl.userinfo(ctx, member)


@component.with_command
@with_description("Reveal some info about the current server")
@tanjun.with_parser
@tanjun.as_message_command("serverinfo", "sinfo")
async def serverinfo(ctx: AoiMessageContext):
    await impl.serverinfo(ctx)


@component.with_command
@with_description("Show all the mentionable roles for this guild")
@tanjun.with_parser
@tanjun.as_message_command("menroles", "mentionableroles")
async def menroles(ctx: AoiMessageContext):
    await impl.menroles(ctx)


@component.with_command
@tanjun.with_greedy_argument("channel", converters=(to_voice_channel,), default=None)
@with_description("Reveal information about a specific voice channel")
@tanjun.with_parser
@tanjun.as_message_command("voiceinfo", "vinfo")
async def voiceinfo(ctx: AoiMessageContext, channel: hikari.GuildVoiceChannel):
    await impl.voiceinfo(ctx, channel)


@component.with_command
@tanjun.with_greedy_argument("channel", converters=(to_text_channel,), default=None)
@with_description("Reveal information about a specific text channel")
@tanjun.with_parser
@tanjun.as_message_command("textinfo", "tcinfo")
async def textinfo(ctx: AoiMessageContext, channel: hikari.GuildTextChannel):
    await impl.textinfo(ctx, channel)


@component.with_command
@tanjun.with_greedy_argument("emoji", converters=(tanjun.to_emoji,), default=None)
@with_description("Reveal information about a specific CUSTOM emoji")
@tanjun.with_parser
@tanjun.as_message_command("emojiinfo", "einfo")
async def emojiinfo(ctx: AoiMessageContext, emoji: hikari.CustomEmoji):
    await impl.emojiinfo(ctx, emoji)


@tanjun.as_loader
def load(client: tanjun.Client):
    client.add_component(component.copy())


@tanjun.as_unloader
def unload(client: tanjun.Client):
    client.remove_component_by_name(component.name)
