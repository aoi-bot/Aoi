from typing import Optional, Union

import aoi
import discord
from discord.ext import commands
from libs.converters import disenable
from libs.misc import null_safe


class Permissions(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.db: Optional[aoi.AoiDatabase] = None
        bot.loop.create_task(self._init())

    @property
    def description(self):
        return "Commands to channelnge command permissions"

    async def _init(self):
        self.bot.logger.info("perms:Waiting for bot")
        await self.bot.wait_until_ready()
        self.db = self.bot.db
        self.bot.logger.info("perms:Ready!")

    @commands.command(brief="View the entire permission channelin", aliases=["lp"])
    async def listperms(self, ctx: aoi.AoiContext):
        perms = await self.db.get_permissions(ctx.guild.id)
        for n, r in enumerate(perms):
            tok = r.split()
            if tok[0] in ["acm", "cm"]:
                tok[1] = f"<#{tok[1]}>"
            if tok[0] in ["arm"]:
                tok[1] = f"<@&{tok[1]}>"
            perms[n] = " ".join(tok)
        await ctx.paginate(perms, title="Permissions list", n=10, numbered=True)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Clear all permissions", aliases=["rp"])
    async def resetperms(self, ctx: aoi.AoiContext):
        await ctx.confirm_coro(
            "Reset all permissions?",
            "Permissions reset",
            "Permission reset cancelled",
            self.db.clear_permissions(ctx.guild.id)
        )

    # region # a_m commands

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable all modules", aliases=["asm"])
    async def allsvrmdls(self, ctx: aoi.AoiContext, enabled: disenable()):
        await self.db.add_permission(ctx.guild.id, f"asm {enabled}")
        await ctx.send_ok(f"`asm {enabled}` added", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable all modules in a channel", aliases=["acm"])
    async def allchnlmdls(self, ctx: aoi.AoiContext, channel: discord.TextChannel,
                          enabled: disenable()):
        await self.db.add_permission(ctx.guild.id, f"acm {channel.id} {enabled}")
        await ctx.send_ok(f"**acm <#{channel.id}> {enabled}** added", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable all modules in a channel", aliases=["axm"])
    async def allcatmdls(self, ctx: aoi.AoiContext, category: discord.CategoryChannel,
                          enabled: disenable()):
        await self.db.add_permission(ctx.guild.id, f"axm {category.id} {enabled}")
        await ctx.send_ok(f"**axm <#{category.id}> {enabled}** added", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable all commands for a role", aliases=["arm"])
    async def allrolemdls(self, ctx: aoi.AoiContext, role: discord.Role, enabled: disenable()):
        await self.db.add_permission(ctx.guild.id, f"arm {role.id} {enabled}")
        await ctx.send_ok(f"**arm <@&{role.id}> {enabled}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable all commands for a role", aliases=["aum"])
    async def allusrmdls(self, ctx: aoi.AoiContext, member: discord.Member, enabled: disenable()):
        await self.db.add_permission(ctx.guild.id, f"aum {member.id} {enabled}")
        await ctx.send_ok(f"**aum <@{member.id}> {enabled}** added.", trash=False)

    # endregion
    
    # region # _m commands
    
    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a module in a channel", aliases=["cm"])
    async def chnlmdl(self, ctx: aoi.AoiContext, channel: discord.TextChannel,
                      enabled: disenable(), module: str):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"cm {channel.id} {enabled} {module}")
        await ctx.send_ok(f"**cm <#{channel.id}> {enabled} {module}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a module server-wide", aliases=["sm"])
    async def svrmdl(self, ctx: aoi.AoiContext, enabled: disenable(), module: str):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"sm {enabled} {module}")
        await ctx.send_ok(f"**sm {enabled} {module}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a module for a role", aliases=["rm"])
    async def rolemdl(self, ctx: aoi.AoiContext, role: discord.Role,
                      enabled: disenable(), module: str):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"rm {role.id} {enabled} {module}")
        await ctx.send_ok(f"**rm <&{role.id}> {enabled} {module}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a module in a category", aliases=["xm"])
    async def catmdl(self, ctx: aoi.AoiContext, category: discord.CategoryChannel,
                      enabled: disenable(), module: str):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"xm {category.id} {enabled} {module}")
        await ctx.send_ok(f"**xm <#{category.id}> {enabled} {module}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a module in a category", aliases=["um"])
    async def usrmdl(self, ctx: aoi.AoiContext, member: discord.Member,
                      enabled: disenable(), module: str):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"um {member.id} {enabled} {module}")
        await ctx.send_ok(f"**um <@{member.id}> {enabled} {module}** added.", trash=False)
        
    # endregion

    # region # _c commands

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a command server-wide", aliases=["sc"])
    async def svrcmd(self, ctx: aoi.AoiContext, enabled: disenable(), command: str):
        cmd = self.bot.get_command(command.lower())
        if not cmd:
            raise commands.BadArgument(f"Command {command} not found")
        await self.db.add_permission(ctx.guild.id, f"sc {enabled} {command}")
        await ctx.send_ok(f"**sc {enabled} {command}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a command for a role", aliases=["rc"])
    async def rolecmd(self, ctx: aoi.AoiContext, role: discord.Role, enabled: disenable(), command: str):
        cmd = self.bot.get_command(command.lower())
        if not cmd:
            raise commands.BadArgument(f"Command {command} not found")
        await self.db.add_permission(ctx.guild.id, f"rc {role.id} {enabled} {command}")
        await ctx.send_ok(f"**rc <&{role.id}> {enabled} {command}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a command server-wide", aliases=["cc"])
    async def chancmd(self, ctx: aoi.AoiContext, channel: discord.TextChannel, enabled: disenable(), command: str):
        cmd = self.bot.get_command(command.lower())
        if not cmd:
            raise commands.BadArgument(f"Command {command} not found")
        await self.db.add_permission(ctx.guild.id, f"cc <#{channel.id}> {enabled} {command}")
        await ctx.send_ok(f"**cc <#{channel.id}> {enabled} {command}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a command for a category", aliases=["xc"])
    async def catcmd(self, ctx: aoi.AoiContext, category: discord.CategoryChannel, enabled: disenable(), command: str):
        cmd = self.bot.get_command(command.lower())
        if not cmd:
            raise commands.BadArgument(f"Command {command} not found")
        await self.db.add_permission(ctx.guild.id, f"xc <#{category.id}> {enabled} {command}")
        await ctx.send_ok(f"**xc <#{category.id}> {enabled} {command}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a command for a category", aliases=["uc"])
    async def cusrcmd(self, ctx: aoi.AoiContext, member: discord.Member, enabled: disenable(), command: str):
        cmd = self.bot.get_command(command.lower())
        if not cmd:
            raise commands.BadArgument(f"Command {command} not found")
        await self.db.add_permission(ctx.guild.id, f"uc <#{member.id}> {enabled} {command}")
        await ctx.send_ok(f"**uc <@{member.id}> {enabled} {command}** added.", trash=False)

    # endregion

    @commands.is_owner()
    @commands.command(brief="Blacklists a user from the bot", aliases=["bl"])
    async def blacklist(self, ctx: aoi.AoiContext, user: Union[discord.User, int]):
        if isinstance(user, int):
            user = null_safe(await self.bot.fetch_unknown_user(user)).id
            if not user:
                raise commands.BadArgument("Invalid User ID")
        else:
            if await self.bot.is_owner(user):
                return await ctx.send_error("You cant blacklist an owner")
            user = user.id
        if user in self.bot.db.blacklisted:
            return await ctx.send_error("User already blacklisted")
        self.bot.db.blacklisted.append(user)
        await self.bot.db.db.execute("insert into blacklist values (?)", (user,))
        await self.bot.db.db.commit()
        await ctx.send_ok("User blacklisted")

    @commands.is_owner()
    @commands.command(brief="Un-blacklists a user from the bot", aliases=["ubl"])
    async def unblacklist(self, ctx: aoi.AoiContext, user: Union[discord.User, int]):
        if isinstance(user, int):
            user = null_safe(await self.bot.fetch_unknown_user(user)).id
            if not user:
                raise commands.BadArgument("Invalid User ID")
        else:
            if await self.bot.is_owner(user):
                return await ctx.send_error("You cant blacklist an owner")
            user = user.id
        if user not in self.bot.db.blacklisted:
            return await ctx.send_error("User not blacklisted")
        self.bot.db.blacklisted.remove(user)
        await self.bot.db.db.execute("delete from blacklist where user=?", (user,))
        await self.bot.db.db.commit()
        await ctx.send_ok("User un-blacklisted")

    @commands.is_owner()
    @commands.command(brief="Checks if an ID is blacklisted, or else prints out blacklisted IDs", aliases=["cbl"])
    async def blacklistcheck(self, ctx: aoi.AoiContext, user: int = None):
        if not user:
            return await ctx.paginate(self.bot.db.blacklisted, 20, "Blacklisted users")
        await ctx.send_info(f"ID {user} is {'' if user in self.bot.db.blacklisted else 'not '} blacklisted")



# arm role on_off
# asm on_off
# axm category on_off
# acm channel on_off
# rm role on_off module
# sm on_off module
# xm category on_off module
# cm channel on_off module
# rc role on_off command
# sc on_off command
# xc category on_off command
# cc channel on_off command

def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Permissions(bot))
