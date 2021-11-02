import hikari
import tanjun

from aoi import AoiContextMixin


def get_color(member: hikari.Member) -> hikari.Color:
    for role in member.get_roles():
        if role.color.rgb != (0, 0, 0):
            return role.color
    return hikari.Color.of(0x000000)


# TODO delete this
# forgot to typehint
# role_ids looks to be already cached, so no need to call get_roles()
# get_members() actually returns {snowflake: member, snowflake: member}, hence the values()


def get_role_members(ctx: AoiContextMixin, role: hikari.Role) -> list[hikari.Member]:
    return [mem for mem in ctx.get_guild().get_members().values() if role.id in mem.role_ids]


def get_role_member_count(ctx: AoiContextMixin, role: hikari.Role) -> int:
    return sum(1 if role.id in member.role_ids else 0 for member in ctx.get_guild().get_members().values())


async def avatar(ctx: AoiContextMixin, member: hikari.Member):
    if not member:
        member = ctx.member

    await ctx.respond(
        embed=hikari.Embed(title=f"{member}'s Avatar", color=get_color(member))
        .set_image(member.avatar_url)
        .set_footer(text=f"ID: {member.id}")
    )


async def roleinfo(ctx: AoiContextMixin, role: hikari.Role):
    await ctx.respond(
        embed=hikari.Embed(title=f"Info for {role}", color=role.color)
        .add_field(name="ID", value=str(role.id), inline=True)
        .add_field(name="Members", value=str(get_role_member_count(ctx, role)), inline=True)
        .add_field(name="Color", value=str(role.color), inline=True)
        .add_field(name="Hoisted", value=str(role.is_hoisted), inline=True)
        .add_field(name="Mentionable", value=str(role.is_mentionable), inline=True)
        .add_field(name="Position", value=str(role.position), inline=True)
        .add_field(name="Created at", value=str(role.created_at.strftime("%c")), inline=True)
    )


async def userinfo(ctx: AoiContextMixin, member: hikari.Member):
    if not member:
        member = ctx.member

    hoisted_roles: list = [r for r in member.get_roles() if r.is_hoisted and r.id != ctx.guild_id]
    normal_roles: list = [r for r in member.get_roles() if not r.is_hoisted and r.id != ctx.guild_id]
    await ctx.respond(
        embed=hikari.Embed(title=f"Info for {member}", color=get_color(member))
        .set_thumbnail(member.avatar_url)
        .add_field(name="ID", value=str(member.id))
        .add_field(name=f"Joined {ctx.get_guild()}", value=str(member.joined_at.strftime("%c")))
        .add_field(name="Joined Discord", value=str(member.created_at.strftime("%c")))
        .add_field(
            name=f"Hoisted Roles: {len(hoisted_roles)}",
            value=" ".join([r.mention for r in hoisted_roles[:-6:-1]]) if hoisted_roles else "None",
        )
        .add_field(
            name=f"Normal Roles: {len(normal_roles)}",
            value=" ".join([r.mention for r in normal_roles[:-6:-1]]) if normal_roles else "None",
        )
        .add_field(
            name="Top Role",
            value=str(member.get_top_role().mention) if len(member.get_roles()) > 1 else "None",
        )
    )


async def serverinfo(ctx: AoiContextMixin):
    guild: hikari.Guild = ctx.get_guild()
    statuses = {"dnd": 0, "idle": 0, "online": 0, "bot": 0, "offline": 0}

    for member in guild.get_members().values():
        if member.is_bot:
            statuses["bot"] += 1
        if not member.get_presence():
            statuses["offline"] += 1
        else:
            statuses[member.get_presence().visible_status] += 1

    num_channels = {}
    for channel in guild.get_channels().values():
        try:
            num_channels[channel.type] += 1
        except KeyError:
            num_channels[channel.type] = 1

    await ctx.get_builder().with_thumbnail(guild.icon_url).add_field("ID", str(ctx.guild_id)).add_field(
        "Created At", guild.created_at.strftime("%c")
    ).add_field("Owner", str(guild.get_member(guild.owner_id))).add_field(
        "Channels",
        f"Text: {num_channels.get(hikari.ChannelType.GUILD_TEXT, 0)}\n"
        f"Voice: {num_channels.get(hikari.ChannelType.GUILD_VOICE, 0)}",
    ).add_field(
        "System Channel", f"<#{guild.system_channel_id}>" if guild.system_channel_id else "None"
    ).add_field(
        "Members", str(len(guild.get_members()))
    ).add_field(
        "Roles", str(len(guild.get_roles()))
    ).add_field(
        "Features", "\n".join(guild.features) if guild.features else "None"
    ).add_field(
        "Breakdown",
        f":green_circle: {statuses['online']} Online\n"
        f":yellow_circle: {statuses['idle']} Idle\n"
        f":red_circle: {statuses['dnd']} DND\n"
        f":white_circle: {statuses['offline']} Offline\n"
        f":robot: {statuses['bot']} Bots",
        inline=True,
    ).send()


async def menroles(ctx: AoiContextMixin):
    roles: list[hikari.Role] = [r for r in ctx.get_guild().get_roles().values() if r.is_mentionable]
    await ctx.get_builder().with_title("Mentionable Roles").with_description(
        " ".join(r.mention for r in roles) if roles else "None"
    ).send()


async def voiceinfo(ctx: AoiContextMixin, channel: hikari.GuildVoiceChannel):
    await ctx.get_builder().with_title(f"Info for {channel}").add_field("ID", str(channel.id)).add_field(
        "Created at", str(channel.created_at.strftime("%c"))
    ).add_field("Max Users", str(channel.user_limit) or "No limit").add_field(
        "Bitrate", f"{channel.bitrate // 1000}kbps"
    ).send()


async def textinfo(self, ctx: AoiContextMixin, channel: hikari.GuildTextChannel):
    ...  # TODO Waiting on text converter


async def emojiinfo(ctx: AoiContextMixin, emoji: hikari.CustomEmoji):
    def _(typ: str) -> str:
        return f"https://cdn.discordapp.com/emojis/{emoji.id}.{typ}?v=1"

    await ctx.get_builder().with_title(f"Info for {emoji}").add_field("ID", str(emoji.id)).add_field(
        "Name", emoji.name
    ).add_field("Animated", str(emoji.is_animated)).add_field(
        "Links",
        f"[jpeg]({_('jpeg')}) "
        f"[png]({_('png')}) "
        f"[webp]({_('webp')}) "
        f"{f'[gif]({emoji})' if emoji.is_animated else ''}",
    ).add_field(
        "Usage", emoji.mention
    ).send()
