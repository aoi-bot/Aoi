import asyncio
import io
import shlex
from typing import List, Union

import discord
from PIL import Image
from PIL import ImageDraw
from discord.ext import commands
from discord.ext.commands import Greedy

import aoi
from libs import conversions
from libs.colors import rgb_gradient, hls_gradient
from libs.converters import AoiColor, rolename


class Roles(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to modify roles"

    def _check_role(self, ctx: aoi.AoiContext, role: discord.Role, action: str = "edit"):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleHierarchyError(f"Role to {action} must be lower than your highest")
        if role >= ctx.me.top_role:
            raise aoi.RoleHierarchyError(f"I can't {action} a role higher than mine")

    def _soft_check_role(self, ctx: aoi.AoiContext, role: discord.Role, action: str = "edit"):
        if role >= ctx.me.top_role:
            raise aoi.RoleHierarchyError(f"I can't {action} a role higher than mine")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is mentionable", aliases=["rolem", "mentionable"])
    async def rolementionable(self, ctx: aoi.AoiContext, *, role: discord.Role):
        self._check_role(ctx, role)
        await role.edit(mentionable=not role.mentionable)
        await ctx.send_info(f"{role.mention} is now {'' if role.mentionable else 'un'}mentionable")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is hoisted", aliases=["roleh", "hoist"])
    async def rolehoist(self, ctx: aoi.AoiContext, *, role: discord.Role):
        self._check_role(ctx, role)
        await role.edit(hoist=not role.hoist)
        await ctx.send_info(f"{role.mention} is now {'' if role.hoist else 'un'}hoisted")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Changes a roles name", aliases=["rren"])
    async def rolerename(self, ctx: aoi.AoiContext, role: discord.Role, *, name: str):
        self._check_role(ctx, role)
        await role.edit(name=name)
        await ctx.send_info(f"Renamed {role.mention}")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Changes a roles color", aliases=["rclr", "roleclr"])
    async def rolecolor(self, ctx: aoi.AoiContext, role: discord.Role, *, color: AoiColor):
        self._check_role(ctx, role)
        await role.edit(colour=color.to_discord_color())
        await ctx.send_info(f"Changed {role.mention}'s color to "
                            f"#{conversions.color_to_string(role.colour)}")

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Creates one or more roles - multiword role names must be quoted.",
                      aliases=["cr"])
    async def createrole(self, ctx: aoi.AoiContext, names: Greedy[rolename()]):

        async def _(name):
            await ctx.guild.create_role(name=name)
            await asyncio.sleep(10)

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

        await ctx.send_ok(f"Created {' '.join(r.mention for r in roles)}", ping=len(roles) > 10)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Moves roles to a position",
                      aliases=["mr"])
    async def moverole(self, ctx: aoi.AoiContext, position: int, roles: Greedy[discord.Role]):
        if not roles:
            raise commands.BadArgument("I need to know what role(s) to move!")
        roles: List[discord.Role] = list(roles)

        for role in roles:
            if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
                raise aoi.RoleHierarchyError(f"{role.mention} must be below your highest role in order for you to move it.")
            if role >= ctx.me.top_role:
                raise aoi.RoleHierarchyError(f"{role.mention} must be above my highest role for me to move it.")
        if not await ctx.confirm(f"Move {' '.join(r.name for r in roles)} to position {position}?",
                                 "Moving roles...",
                                 "Role move cancelled"):
            return

        n = 0

        async def do_op():
            nonlocal n
            for r in roles:
                await r.edit(position=position)

        await ctx.trigger_typing()
        if len(roles) > 3:
            await ctx.send_info(f"Moving {len(roles)} roles. Will take at least {len(roles)}s")
        await self.bot.create_task(ctx, do_op(), lambda: f"{n}/{(len(roles))}")
        await ctx.send_ok(f"Moved {' '.join('`' + r.name + '`' for r in roles)}", ping=len(roles) > 10)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Deletes one or more roles",
                      aliases=["dr"])
    async def deleterole(self, ctx: aoi.AoiContext, roles: Greedy[discord.Role]):
        if not roles:
            raise commands.BadArgument("I need to know what role(s) to delete!")
        roles: List[discord.Role] = list(roles)
        for role in roles:
            self._check_role(ctx, role)
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

        await ctx.trigger_typing()
        if len(roles) > 3:
            await ctx.send_info(f"Deleting {len(roles)} roles. Will take at least {len(roles)}s")
        await self.bot.create_task(ctx, do_op(), lambda: f"{n}/{(len(roles))}")
        await ctx.send_ok(f"Deleted {' '.join('`' + r.name + '`' for r in roles)}", ping=len(roles) > 10)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.command(
        brief="Colors roles as an RGB gradient between colors",
        aliases=["rolegrad"],
        flags={"hls": (None, "Use HLS")}
    )
    async def rolegradient(self, ctx: aoi.AoiContext, color1: AoiColor, color2: AoiColor,
                           roles: Greedy[discord.Role]):
        hls = "hls" in ctx.flags
        roles: List[discord.Role] = list(roles)
        for role in roles:
            self._check_role(ctx, role)
        num = len(roles)
        colors = hls_gradient(color1, color2, num) if hls else rgb_gradient(color1, color2, num)
        img = Image.new("RGB", (240, 48))
        await ctx.trigger_typing()
        img_draw = ImageDraw.Draw(img)
        n = 0
        buf = io.BytesIO()

        async def do_op():
            nonlocal n
            for idx, clr in enumerate(colors):
                await asyncio.sleep(0.5)
                await roles[idx].edit(color=AoiColor(*clr).to_discord_color())
                img_draw.rectangle([
                    (idx * 240 / num, 0),
                    ((idx + 1) * 240 / num, 48)
                ], fill=tuple(map(int, clr)))
            img.save(buf, format="PNG")

        await self.bot.create_task(ctx, do_op(), lambda: f"{n}/{num}")
        await ctx.embed(title="Roles colored according to gradient",
                        description=" ".join("#" + "".join(hex(x)[2:] for x in c) for c in colors),
                        image=buf)

    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(
        manage_roles=True,
        manage_guild=True
    )
    @commands.command(
        brief="Adds a role to everyone - shows up in `mytasks` and may take a while.",
        flags={"ignorebots": (None, "Ignore bots"), 
               "withrole": (discord.Role, "Only adds a role to people with the supplied role")}
    )
    async def roleall(self, ctx: aoi.AoiContext, role: discord.Role):
        flags = ctx.flags
        ignore_bots = "ignorebots" in flags
        with_role = flags.get("withrole", None)
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise aoi.RoleHierarchyError(f"{role.mention} must be below your highest role in order for you to delete it.")
        if role >= ctx.me.top_role:
            raise aoi.RoleHierarchyError(f"{role.mention} must be above my highest role for me to delete it.")
        members: List[discord.Member] = list(filter(lambda x: role.id not in [r.id for r in x.roles], # noqa
                                                    ctx.guild.members))
        if ignore_bots:
            members = [member for member in members if not member.bot]
        if with_role:
            members = [member for member in members if with_role.id in [r.id for r in member.roles]]
        await ctx.send_ok(f"Adding {role.mention} to {len(members)} that don't have it" +
                          (", while ignoring bots" if ignore_bots else "") +
                          ". This will take at " +
                          f"least {len(members) // 2}s")
        n = 0

        async def do_op():
            nonlocal n
            for m in members:
                if m.bot and ignore_bots:
                    continue
                if with_role and with_role.id not in [r.id for r in m.roles]:
                    continue
                await m.add_roles(role, reason=f"roleall by {ctx.author} | {ctx.author.id}")
                n += 1
                await aoi.asyncio.sleep(1)

        await ctx.trigger_typing()
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
        await ctx.paginate([f"{r.position:>3} "
                            f"{'M' if r.mentionable else '·'}"
                            f"{'C' if r.color.to_rgb() != (0, 0, 0) else '·'}"
                            f"{'H' if r.hoist else '·'} "
                            f"{discord.utils.escape_markdown(r.name)}"
                            for r in ctx.guild.roles[::-1]], 20, "Role list",
                           fmt="```Pos     Name\n%s```\n"
                               "M-Mentionable  —  "
                               "H-Hoisted  —  "
                               "C-Colored")

    @commands.command(
        brief="List the server's self-assignable roles",
        aliases=["lsr"]
    )
    async def listselfroles(self, ctx: aoi.AoiContext):
        if ctx.guild.id not in self.bot.db.self_roles or not self.bot.db.self_roles[ctx.guild.id]:
            return await ctx.send_error(f"{ctx.guild} has no self-assignable roles")

        # remove invalid self-roles
        lost_roles = []
        for r in self.bot.db.self_roles[ctx.guild.id]:
            if not ctx.guild.get_role(r):
                lost_roles.append(r)
        if lost_roles:
            await ctx.trigger_typing()
        for r in lost_roles:
            await self.bot.db.remove_self_role(ctx.guild, r)

        await ctx.send_info("Self-assignable roles on this server\n" +
                            "\n".join(
                                f"<@&{i}>" for i in self.bot.db.self_roles[ctx.guild.id]
                            ))

    @commands.has_permissions(manage_roles=True)
    @commands.command(
        brief="Adds a self-assignable to the server",
        aliases=["asr", "asrole"]
    )
    async def addselfrole(self, ctx: aoi.AoiContext, *, role: discord.Role):
        self._soft_check_role(ctx, role, "add")
        await self.bot.db.add_self_role(ctx.guild, role)
        await ctx.send_ok(f"{role.mention} added to self-assignable roles")

    @commands.has_permissions(manage_roles=True)
    @commands.command(
        brief="Adds a self-assignable to the server",
        aliases=["rsr", "rsrole"]
    )
    async def removeselfrole(self, ctx: aoi.AoiContext, *, role: discord.Role):
        await self.bot.db.remove_self_role(ctx.guild, role)
        await ctx.send_ok(f"{role.mention} removed from self-assignable roles")

    @commands.command(
        brief="Adds a self-assignable role to you"
    )
    async def addrole(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if ctx.guild.id not in self.bot.db.self_roles or not self.bot.db.self_roles[ctx.guild.id]:
            return await ctx.send_error(f"{ctx.guild} has no self-assignable roles")
        self._soft_check_role(ctx, role, "add")
        # remove invalid self-roles
        lost_roles = []
        for r in self.bot.db.self_roles[ctx.guild.id]:
            if not ctx.guild.get_role(r):
                lost_roles.append(r)
        if lost_roles:
            await ctx.trigger_typing()
        for r in lost_roles:
            await self.bot.db.remove_self_role(ctx.guild, r)

        if role.id not in self.bot.db.self_roles[ctx.guild.id]:
            return await ctx.send_error(f"{role.mention} is not self-assignable")

        if role.id in [r.id for r in ctx.author.roles]:
            return await ctx.send_error(f"You already have {role.mention}")

        await ctx.author.add_roles(role)
        await ctx.send_ok("Role added!")

    @commands.command(
        brief="Removes a self-assignable role from you"
    )
    async def removerole(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if ctx.guild.id not in self.bot.db.self_roles or not self.bot.db.self_roles[ctx.guild.id]:
            return await ctx.send_error(f"{ctx.guild} has no self-assignable roles")
        self._soft_check_role(ctx, role, "remove")
        # remove invalid self-roles
        lost_roles = []
        for r in self.bot.db.self_roles[ctx.guild.id]:
            if not ctx.guild.get_role(r):
                lost_roles.append(r)
        if lost_roles:
            await ctx.trigger_typing()
        for r in lost_roles:
            await self.bot.db.remove_self_role(ctx.guild, r)

        if role.id not in self.bot.db.self_roles[ctx.guild.id]:
            return await ctx.send_error(f"{role.mention} is not self-assignable")

        if role.id not in [r.id for r in ctx.author.roles]:
            return await ctx.send_error(f"You don't have {role.mention}")

        await ctx.author.remove_roles(role)
        await ctx.send_ok("Role removed!")

    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.command(
        brief="Creates color roles"
    )
    async def colorroles(self, ctx: aoi.AoiContext):
        colors = {
            "Red": 0xe74c3c,
            "Orange": 0xe67e22,
            "Yellow": 0xf1c40f,
            "Green": 0x2ecc71,
            "Blue": 0x3498db,
            "Purple": 0x9b59b6,
            "Brown": 0x8b4513,
            "Tan": 0xbb8553,
            "Gray": 0x888888
        }
        created = []

        await ctx.trigger_typing()

        for color, value in colors.items():
            created.append(await ctx.guild.create_role(name=color, color=discord.Colour(value)))
            await asyncio.sleep(0.5)

        await ctx.send_info(f"Created " + " ".join(r.mention for r in created))


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Roles(bot))
