import asyncio
import io
from typing import List, Union

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
        async def _(name):
            await ctx.guild.create_role(name=name)
            await asyncio.sleep(10)

        names = names.split(";")

        if len(names) > 3:
            conf = await ctx.confirm("Create roles: " + (" ".join(f"`{n}`" for n in names) + "?"),
                                     "Creating roles...",
                                     "Role creation cancelled")
            if not conf:
                return
        n = 0
        roles = []
        num = len(names)

        async def do_op():
            nonlocal n
            for r in names:
                roles.append(await ctx.guild.create_role(name=r))
                await asyncio.sleep(1)
                n += 1

        await ctx.send_info(f"Creating {num} roles. Will take at least {num}s")
        await self.bot.create_task(ctx, do_op(), lambda: f"{n}/{num}")

        await ctx.send_ok(f"Created {' '.join(r.mention for r in roles)}", ping=True)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Deletes one or more roles",
                      aliases=["dr"])
    async def deleterole(self, ctx: aoi.AoiContext, roles: Greedy[discord.Role]):
        if not roles:
            raise commands.BadArgument("I need to know what role(s) to delete!")
        roles: List[discord.Role] = list(roles)
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
        n = 0

        async def do_op():
            nonlocal n
            for r in roles:
                await r.delete()
                await asyncio.sleep(1)
                n += 1

        if len(roles) > 3:
            await ctx.send_info(f"Deleting {len(roles)} roles. Will take at least {len(roles)}s")
        await self.bot.create_task(ctx, do_op(), lambda: f"{n}/{(len(roles))}")
        await ctx.send_ok(f"Deleted {' '.join('`' + r.name + '`' for r in roles)}", ping=True)

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
            await asyncio.sleep(0.5)
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

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(
        manage_roles=True,
        manage_guild=True
    )
    @commands.command(
        brief="Adds a role to everyone - shows up in `mytasks` and may take a while."
    )
    async def roleall(self, ctx: aoi.AoiContext, role: discord.Role):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleError(f"{role.mention} must be below your highest role in order for you to delete it.")
        if role >= ctx.me.top_role:
            raise aoi.RoleError(f"{role.mention} must be above my highest role for me to delete it.")
        members: List[discord.Member] = list(filter(lambda x: role.id not in [r.id for r in x.roles],
                                                    ctx.guild.members))
        await ctx.send_ok(f"Adding {role.mention} to {len(members)} that don't have it. This will take at "
                          f"least {len(members) // 2}s")
        n = 0

        async def do_op():
            nonlocal n
            for m in members:
                await m.add_roles(role, reason=f"roleall by {ctx.author} | {ctx.author.id}")
                n += 1
                await aoi.asyncio.sleep(1)

        await self.bot.create_task(ctx, do_op(), lambda: f"{n}/{len(members)}")

        await ctx.done_ping()

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(
        manage_roles=True,
        manage_guild=True
    )
    @commands.max_concurrency(1, per=commands.BucketType.guild)
    @commands.command(
        brief="Adds a role users get on join",
        aliases=["aarole"]
    )
    async def addautorole(self, ctx: aoi.AoiContext, role: discord.Role):
        if ctx.guild.id in self.bot.db.auto_roles and len(self.bot.db.auto_roles[ctx.guild.id]) >= self.bot.config[
            "max_auto_role"]:  # noqa
            await ctx.send_error(
                f"You are only allowed to have {self.bot.config['max_auto_role']} autoroles per server. "  # noqa
                f"You can list the current autoroles with `{ctx.prefix}larole` and delete one with "
                f"`{ctx.prefix}darole`")
        await self.bot.db.add_auto_role(ctx.guild, role)
        await ctx.send_ok(f"{role.mention} added to the list of automatically assigned roles on this server. You can "
                          f"view the list with `{ctx.prefix}larole`")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(
        manage_roles=True,
        manage_guild=True
    )
    @commands.max_concurrency(1, per=commands.BucketType.guild)
    @commands.command(
        brief="Deletes a role users get on join",
        aliases=["darole"]
    )
    async def delautorole(self, ctx: aoi.AoiContext, role: Union[discord.Role, int]):
        was_role = False
        if isinstance(role, discord.Role):
            role = role.id
            was_role = True
        if ctx.guild.id not in self.bot.db.auto_roles or role not in self.bot.db.auto_roles[ctx.guild.id]:
            return await ctx.send_error(f"{'<@&' if was_role else ''}{role}{'>' if was_role else ''} is not in the "
                                        f"list if automatically assigned roles in this server. You can "
                                        f"view the list with `{ctx.prefix}larole`")
        await self.bot.db.del_auto_role(ctx.guild, role)
        await ctx.send_ok(f"{'<@&' if was_role else ''}{role}{'>' if was_role else ''} deleted from the list of "
                          f"automatically assigned roles")

    @commands.max_concurrency(1, per=commands.BucketType.guild)
    @commands.command(
        brief="Shows the list of roles a user gets on join",
        aliases=["larole"]
    )
    async def listautoroles(self, ctx: aoi.AoiContext):
        if ctx.guild.id not in self.bot.db.auto_roles or not self.bot.db.auto_roles[ctx.guild.id]:
            return await ctx.send_info("There are no automatically assigned roles on this server.")

        # remove invalid roles from the auto role list
        lost_roles = []
        for r in self.bot.db.auto_roles[ctx.guild.id]:
            if not ctx.guild.get_role(r):
                lost_roles.append(r)
        if lost_roles:
            await ctx.trigger_typing()
        for r in lost_roles:
            await self.bot.db.del_auto_role(ctx.guild, r)

        if ctx.guild.id not in self.bot.db.auto_roles or not self.bot.db.auto_roles[ctx.guild.id]:
            return await ctx.send_info("There are no automatically assigned roles on this server.")

        await ctx.send_info("Automatically assigned roles on this server\n" +
                            "\n".join(
                                f"<@&{i}>" for i in self.bot.db.auto_roles[ctx.guild.id]
                            ))

    @commands.command(
        brief="Lists the server's roles"
    )
    async def roles(self, ctx: aoi.AoiContext):
        await ctx.paginate([f"{r.position} - {discord.utils.escape_markdown(r.name)}"
                           for r in ctx.guild.roles[::-1]], 20, "Role list")

def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Roles(bot))
