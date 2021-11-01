import hikari
import tanjun


def get_color(member: hikari.Member) -> hikari.Color:
    for role in member.get_roles():
        if role.color.rgb != (0, 0, 0):
            return role.color
    return hikari.Color.of(0x000000)


# TODO delete this
# forgot to typehint
# role_ids looks to be already cached, so no need to call get_roles()
# get_members() actually returns {snowflake: member, snowflake: member}, hence the values()

def get_role_members(ctx: tanjun.abc.Context, role: hikari.Role) -> list[hikari.Member]:
    return [mem for mem in ctx.get_guild().get_members().values() if role.id in mem.role_ids]


def get_role_member_count(ctx: tanjun.abc.Context, role: hikari.Role) -> int:
    return sum(1 if role.id in member.role_ids else 0
               for member in ctx.get_guild().get_members().values())


async def avatar(ctx: tanjun.abc.Context, member: hikari.Member):
    if not member:
        member = ctx.member

    await ctx.respond(
        embed=hikari.Embed(title=f"{member}'s Avatar", color=get_color(member))
            .set_image(member.avatar_url)
            .set_footer(text=f"ID: {member.id}")
    )


async def roleinfo(ctx: tanjun.abc.Context, role: hikari.Role):
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


async def userinfo(ctx: tanjun.abc.Context, member: hikari.Member):
    if not member:
        member = ctx.member

    hoisted_roles = [r for r in member.get_roles() if r.is_hoisted and r.id != ctx.get_guild().id]
    normal_roles = [r for r in member.get_roles() if not r.is_hoisted and r.id != ctx.get_guild().id]
    await ctx.respond(
        embed=hikari.Embed(
            title=f"Info for {member}",
            color=get_color(member)
        )
        .set_thumbnail(member.avatar_url)
        .add_field(
            name="ID",
            value=str(member.id)
        )
        .add_field(
            name=f"Joined {ctx.get_guild()}",
            value=str(member.joined_at.strftime("%c"))
        )
        .add_field(
            name="Joined Discord",
            value=str(member.created_at.strftime("%c"))

        )
        .add_field(
            name=f"Hoisted Roles: {len(hoisted_roles)}",
            value=" ".join([r.mention for r in hoisted_roles[:-6:-1]]) if hoisted_roles else "None"
        )
        .add_field(
        name=f"Normal Roles: {len(normal_roles)}",
        value=" ".join([r.mention for r in normal_roles[:-6:-1]]) if normal_roles else "None"
        )
        .add_field(
            name="Top Role",
            value=str(member.get_top_role().mention) if len(member.get_roles()) > 1 else "None"
        )
    )