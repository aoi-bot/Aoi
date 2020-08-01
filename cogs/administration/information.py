import discord
from discord.ext import commands

import aoi


class Information(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.command(brief="Shows info on a user", aliases=["uinfo"])
    async def userinfo(self, ctx: aoi.AoiContext, member: discord.Member = None):
        if not member:
            member = ctx.author
        joined_at = member.joined_at.strftime("%c")
        created_at = member.created_at.strftime("%c")
        r: discord.Role
        hoisted_roles = [r for r in member.roles if r.hoist]
        normal_roles = member.roles
        await ctx.embed(
            title=f"Info for {member}",
            fields=[
                ("ID", member.id),
                ("Joined Server", joined_at),
                ("Joined Discord", created_at),
                (f"Hoisted Roles ({len(hoisted_roles)}) ",
                 " ".join([r.mention for r in hoisted_roles[0:5]]) if hoisted_roles
                 else "None"),
                (f"Normal Roles ({len(normal_roles) - 1})",
                 " ".join([r.mention for r in normal_roles[1:5] if r.id not in
                           [x.id for x in hoisted_roles]]) if len(normal_roles) > 1
                 else "None"),
                ("Top Role", member.roles[-1].mention),
                ("Ansura Profile", f"https://www.ansura.xyz/profile/{member.id}")
            ],
            clr=member.color,
            thumbnail=member.avatar_url
        )


    @commands.command(brief="Shows info on a role", aliases=["rinfo"])
    async def roleinfo(self, ctx: aoi.AoiContext, role: discord.Role):
        await ctx.embed(
            clr=role.colour,
            title=f"Info for {role}",
            fields=[
                ("ID", role.id),
                ("Members", len(role.members)),
                ("Color", conversions.color_to_string())
            ]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Information(bot))
