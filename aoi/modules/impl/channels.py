import hikari

from aoi import AoiContextMixin


async def nsfw(ctx: AoiContextMixin, channel: hikari.GuildTextChannel):
    if not channel:
        channel = ctx.get_channel()
    await channel.edit(nsfw=not channel.is_nsfw)
    await ctx.get_builder().as_ok().with_description(
        f"{channel.mention}'s NSFW flag has been marked {'off' if channel.is_nsfw else 'on'}"
    ).send()
