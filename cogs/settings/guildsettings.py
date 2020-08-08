import discord
from discord.ext import commands

import aoi
from libs import conversions


class GuildSettings(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Change and view Aoi's configuration in your server"

    async def okcolor(self, ctx: aoi.AoiContext, color: discord.Color):
        await self.bot.db.set_ok_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    async def infocolor(self, ctx: aoi.AoiContext, color: discord.Color):
        await self.bot.db.set_info_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    async def errorcolor(self, ctx: aoi.AoiContext, color: discord.Color):
        await self.bot.db.set_error_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    @commands.has_guild_permissions(manage_guild=True)
    @commands.command(brief="Set server config")
    async def config(self, ctx: aoi.AoiContext, setting: str, value: str):
        setting = setting.lower()
        color_funcs = {
            "okcolor": self.okcolor,
            "errorcolor": self.errorcolor,
            "infocolor": self.infocolor
        }
        if setting in color_funcs:
            conv = commands.ColourConverter()
            try:
                color: discord.Colour = await conv.convert(ctx, value)
            except commands.CommandError:
                return await ctx.send_error("Invalid color")
            # noinspection PyArgumentList
            return await color_funcs[setting](ctx, color)
        if setting == "prefix":
            await self.bot.db.set_prefix(ctx.guild.id, value)
            return await ctx.send_ok(f"Prefix set to `{value}`")
        await ctx.send_error("Invalid config")

    @commands.has_guild_permissions(manage_guild=True)
    @commands.command(brief="Lists current configs for the server.")
    async def configs(self, ctx: aoi.AoiContext):
        colors = self.bot.db.guild_settings[ctx.guild.id]
        await ctx.embed(
            title="Aoi Configs",
            fields=[
                ("Embed Colors", f"ErrorColor: `{conversions.hex_color_to_string(colors.error_color)}`\n"
                                 f"InfoColor: `{conversions.hex_color_to_string(colors.info_color)}`\n"
                                 f"OKColor: `{conversions.hex_color_to_string(colors.ok_color)}`"),
                ("Prefix", self.bot.db.prefixes[ctx.guild.id])
            ]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(GuildSettings(bot))
