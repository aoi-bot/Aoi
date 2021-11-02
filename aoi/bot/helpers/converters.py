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
import re
import typing

import hikari
import tanjun

BARE_ID = re.compile(r"\d{18,21}")
CHANNEL = re.compile(r"<#\d{18,21}>")
ROLE = re.compile(r"<@&\d{18,21}>")
USER = re.compile(r"<@!?\d{18,21}>")


async def to_voice_channel(
    argument: str, ctx: tanjun.abc.Context = tanjun.injected(type=tanjun.abc.Context)
) -> hikari.GuildVoiceChannel:
    if re.match(BARE_ID, argument):
        channel_id = hikari.Snowflake(argument)
    else:
        for snowflake, channel in ctx.get_guild().get_channels().items():
            if channel.type == hikari.ChannelType.GUILD_VOICE and channel.name.lower() == argument.lower():
                channel_id = snowflake
                break
        else:
            raise ValueError("Argument passed was not a valid voice channel")
    return typing.cast(hikari.GuildVoiceChannel, ctx.get_guild().get_channel(channel_id))


async def to_text_channel(
    argument: str, ctx: tanjun.abc.Context = tanjun.injected(type=tanjun.abc.Context)
) -> hikari.GuildTextChannel:
    if re.match(BARE_ID, argument):
        channel_id = hikari.Snowflake(argument)
    elif re.match(CHANNEL, argument):
        channel_id = hikari.Snowflake(argument[2:-1])
    else:
        for snowflake, channel in ctx.get_guild().get_channels().items():
            if channel.type == hikari.ChannelType.GUILD_TEXT and channel.name.lower() == argument.lower():
                channel_id = snowflake
                break
        else:
            raise ValueError("Argument passed was not a valid text channel")
    return typing.cast(hikari.GuildTextChannel, ctx.get_guild().get_channel(channel_id))
