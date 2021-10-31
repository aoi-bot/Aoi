import hikari
import tanjun


def get_color(member: hikari.Member):
    for role in member.get_roles():
        if role.color.rgb != (0, 0, 0):
            return role.color
        return hikari.Color.of(0x000000)


def get_role_members(ctx: tanjun.abc.Context, role: hikari.Role):
    members = []
    for mem in ctx.get_guild().get_members():
        if role in mem.get_roles():
            members.append(mem)
    return members


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
        .add_field(name="ID", value=str(role.id))
        .add_field(name="Members", value=str(get_role_members(ctx, role)))
        .add_field(name="Color", value=str(role.color))
        .add_field(name="Hoisted", value=str(role.is_hoisted))
        .add_field(name="Mentionable", value=str(role.is_mentionable))
        .add_field(name="Position", value=str(role.position))
        .add_field(name="Created at", value=str(role.created_at.strftime("%c")))
    )
