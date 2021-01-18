from typing import Optional

import aoi
import discord
from discord.ext import commands
from libs.converters import disenable


class Permissions(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.db: Optional[aoi.AoiDatabase] = None
        bot.loop.create_task(self._init())

    @property
    def description(self):
        return "Commands to change command permissions"

    async def _init(self):
        self.bot.logger.info("perms:Waiting for bot")
        await self.bot.wait_until_ready()
        self.db = self.bot.db
        self.bot.logger.info("perms:Ready!")

    @commands.command(brief="View the entire permission chain", aliases=["lp"])
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
    @commands.command(brief="Disable or enable a module in a channel", aliases=["cm"])
    async def chnlmdl(self, ctx: aoi.AoiContext, channel: discord.TextChannel,
                      enabled: disenable(), module):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"cm {channel.id} {enabled} {module}")
        await ctx.send_ok(f"**cm <#{channel.id}> {enabled} {module}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a command server-wide", aliases=["sc"])
    async def svrcmd(self, ctx: aoi.AoiContext, command: str, enabled: disenable()):
        cmd = self.bot.get_command(command.lower())
        if not cmd:
            raise commands.BadArgument(f"Command {command} not found")
        await self.db.add_permission(ctx.guild.id, f"sc {command} {enabled}")
        await ctx.send_ok(f"**sc {command} {enabled}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable a module server-wide", aliases=["sm"])
    async def svrmdl(self, ctx: aoi.AoiContext, module: str, enabled: disenable()):
        module = self.bot.find_cog(module)[0]
        await self.db.add_permission(ctx.guild.id, f"sm {module} {enabled}")
        await ctx.send_ok(f"**sm {module} {enabled}** added.", trash=False)

    @commands.has_permissions(administrator=True)
    @commands.command(brief="Disable or enable all commands for a role", aliases=["arm"])
    async def allrolemdls(self, ctx: aoi.AoiContext, role: discord.Role, enabled: disenable()):
        await self.db.add_permission(ctx.guild.id, f"arm {role.id} {enabled}")
        await ctx.send_ok(f"**arm {role.name} {enabled}** added.", trash=False)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Permissions(bot))
