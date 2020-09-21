import io
from typing import List

import discord
from PIL import Image
from PIL import ImageDraw
from discord.ext import commands
from discord.ext.commands import Greedy

import aoi
from libs import conversions


class Roles(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to modify roles"

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is mentionable", aliases=["rolem", "mentionable"])
    async def rolementionable(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("Im can't edit a role higher than mine")
        await role.edit(mentionable=not role.mentionable)
        await ctx.send_info(f"{role.mention} is now {'' if role.mentionable else 'un'}mentionable")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is hoisted", aliases=["roleh", "hoist"])
    async def rolehoist(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("Im can't edit a role higher than mine")
        await role.edit(hoist=not role.hoist)
        await ctx.send_info(f"{role.mention} is now {'' if role.hoist else 'un'}hoisted")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Changes a roles name", aliases=["rren"])
    async def rolerename(self, ctx: aoi.AoiContext, role: discord.Role, *, name: str):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleError("Im can't edit a role higher than mine")
        await role.edit(name=name)
        await ctx.send_info(f"Renamed {role.mention}")

    @commands.bot_has_permissions(manage_roles=True)
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

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Creates one or more roles - rolenames must be separated by semicolons.",
                      aliases=["cr"])
    async def createrole(self, ctx: aoi.AoiContext, *, names: str):
        roles = [await ctx.guild.create_role(name=name) for name in names.split(";")]
        if len(roles) > 3:
            conf = await ctx.confirm("Create roles: " + (" ".join(f"`{n}`" for n in roles) + "?"),
                                     "Creating roles...",
                                     "Role creation cancelled")
            if not conf:
                return
        await ctx.send_ok(f"Created {' '.join(r.mention for r in roles)}")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Deletes one or more roles",
                      aliases=["dr"])
    async def deleterole(self, ctx: aoi.AoiContext, roles: Greedy[discord.Role]):
        for role in roles:
            if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
                raise aoi.RoleError(f"{role.mention} must be below your highest role in order for you to delete it.")
            if role >= ctx.me.top_role:
                raise aoi.RoleError(f"{role.mention} must be above my highest role for me to delete it.")
        if len(roles) > 3:
            conf = await ctx.confirm(f"Delete {' '.join(r.name for r in roles)}?",
                                     "Deleting roles...",
                                     "Role deletion cancelled")
            if not conf:
                return
        await ctx.send_ok(f"Deleted {' '.join('`' + r.name + '`' for r in roles)}")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(
        brief="Colors roles as an RGB gradient between colors",
        aliases=["rolegrad"]
    )
    async def rolegradient(self, ctx: aoi.AoiContext, color1: discord.Colour, color2: discord.Colour,
                           roles: Greedy[discord.Role]):
        roles: List[discord.Role] = list(roles)
        num = len(roles)
        rgb, rgb2 = color1.to_rgb(), color2.to_rgb()
        steps = [(rgb[x] - rgb2[x]) / (num - 1) for x in range(3)]
        colors = list(reversed([tuple(map(int, (rgb2[x] + steps[x] * n for x in range(3)))) for n in range(num)]))
        img = Image.new("RGB", (240, 48))
        img_draw = ImageDraw.Draw(img)
        for n, clr in enumerate(colors):
            await roles[n].edit(color=int("".join(hex(x)[2:] for x in clr), 16))
            img_draw.rectangle([
                (n * 240 / num, 0),
                ((n + 1) * 240 / num, 48)
            ], fill=tuple(map(int, clr)))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(title="Roles colored according to gradient",
                        description=" ".join("#" + "".join(hex(x)[2:] for x in c) for c in colors),
                        image=buf)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Roles(bot))
