import discord
from discord.ext import commands

import aoi
from libs import conversions


class Roles(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is mentionable", aliases=["rolem", "mentionable"])
    async def rolementionable(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("I can't edit a role higher than mine")
        await role.edit(mentionable=not role.mentionable)
        await ctx.send_info(f"{role.mention} is now {'' if role.mentionable else 'un'}mentionable")

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is hoisted", aliases=["roleh", "hoist"])
    async def rolehoist(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("I can't edit a role higher than mine")
        await role.edit(hoist=not role.hoist)
        await ctx.send_info(f"{role.mention} is now {'' if role.hoist else 'un'}hoisted")

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Changes a roles name", aliases=["rren"])
    async def rolerename(self, ctx: aoi.AoiContext, role: discord.Role, *, name: str):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("I can't edit a role higher than mine")
        await role.edit(name=name)
        await ctx.send_info(f"Renamed {role.mention}")

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Changes a roles color", aliases=["rclr", "roleclr"])
    async def rolecolor(self, ctx: aoi.AoiContext, role: discord.Role, *, color: discord.Colour):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("I can't edit a role higher than mine")
        await role.edit(colour=color)
        await ctx.send_info(f"Changed {role.mention}'s color to "
                            f"#{conversions.color_to_string(role.colour)}")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Roles(bot))
