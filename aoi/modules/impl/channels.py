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


import hikari

from aoi import AoiContextMixin


async def nsfw(ctx: AoiContextMixin, channel: hikari.GuildTextChannel):
    if not channel:
        channel = ctx.get_channel()
    await channel.edit(nsfw=not channel.is_nsfw)
    await ctx.get_builder().as_ok().with_description(
        f"{channel.mention}'s NSFW flag has been marked {'off' if channel.is_nsfw else 'on'}"
    ).send()


async def chanmute(ctx: AoiContextMixin, member: hikari.Member, channel: hikari.GuildTextChannel):
    if not channel:
        channel = ctx.get_channel()
    await channel.edit_overwrite(target=member, deny=hikari.Permissions.SEND_MESSAGES)
    await ctx.get_builder().as_ok().with_description(f"{member.mention} muted in {channel.mention}").send()


async def remchanmute(ctx: AoiContextMixin, member: hikari.Member, channel: hikari.GuildTextChannel):
    if not channel:
        channel = ctx.get_channel()
    await channel.edit_overwrite(target=member, allow=hikari.Permissions.SEND_MESSAGES)
    await ctx.get_builder().as_ok().with_description(f"{member.mention} unmuted in {channel.mention}").send()


async def lockout(ctx: AoiContextMixin, member: hikari.Member, channel: hikari.GuildTextChannel):
    if not channel:
        channel = ctx.get_channel()
    await channel.edit_overwrite(target=member, deny=hikari.Permissions.VIEW_CHANNEL)
    await ctx.get_builder().as_ok().with_description(f"{member.mention} locked out of {channel.mention}").send()
