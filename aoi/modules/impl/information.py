from typing import Union

import hikari
import tanjun

async def avatar(ctx: Union[tanjun.abc.MessageContext, tanjun.SlashContext], member: hikari.Member):

    color = hikari.Color.of(0x000000)
    for role in member.get_roles():
        if role.color.rgb != (0, 0, 0):
            color = role.color

    await ctx.respond(
        embed=hikari.Embed(
            title=f"{member}'s Avatar",
            color=color
        ).set_image(member.avatar_url)
    )
