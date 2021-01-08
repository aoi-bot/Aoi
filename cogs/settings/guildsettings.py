import aoi
from discord.ext import commands
from libs import conversions
from libs.conversions import escape
from libs.converters import AoiColor


class GuildSettings(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return f"Change and view {self.bot.user.name if self.bot.user else ''}'s configuration in your server"

    async def okcolor(self, ctx: aoi.AoiContext, color: AoiColor):
        await self.bot.db.set_ok_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    async def infocolor(self, ctx: aoi.AoiContext, color: AoiColor):
        await self.bot.db.set_info_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    async def errorcolor(self, ctx: aoi.AoiContext, color: AoiColor):
        await self.bot.db.set_error_color(ctx.guild.id, conversions.color_to_string(color))
        await ctx.send_ok("Color changed!")

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Set #BOT#'s prefix")
    async def prefix(self, ctx: aoi.AoiContext, *, prefix: str = None):
        if not prefix:
            return await ctx.send_ok(f"Prefix is set to `{escape(self.bot.db.prefixes[ctx.guild.id], ctx)}`")
        await self.bot.db.set_prefix(ctx.guild.id, prefix)
        return await ctx.send_ok(f"Prefix set to `{escape(prefix, ctx)}`")

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Set server config")
    async def config(self, ctx: aoi.AoiContext, setting: str, *, value: str):
        setting = setting.lower()
        color_funcs = {
            "okcolor": self.okcolor,
            "errorcolor": self.errorcolor,
            "infocolor": self.infocolor
        }
        if setting in color_funcs:
            try:
                color: AoiColor = await AoiColor.convert(ctx, value)
            except commands.CommandError:
                return await ctx.send_error("Invalid color")
            # noinspection PyArgumentList
            return await color_funcs[setting](ctx, color)
        if setting == "prefix":
            await self.bot.db.set_prefix(ctx.guild.id, value)
            return await ctx.send_ok(f"Prefix set to `{escape(value, ctx)}`")
        if setting == "currencygain":
            try:
                v = int(value)
                if v < 0 or v > 50:
                    return await ctx.send_error("Gain value must be between 0 and 50")
                await self.bot.db.set_currency_gain(ctx.guild, v)
                return await ctx.send_ok(f"Currency gain " + ("turned off" if not v else f"set to {v}/3min"))
            except ValueError:
                return await ctx.send_error("Gain value must be a number between 0 and 50")
        if setting == "embeds":
            if value.lower() not in ["true", "false"]:
                return await ctx.send_error("Value must be true or false")
            await self.bot.db.set_reply_embeds(ctx.guild.id, value == "true")
            return await ctx.send_ok(f"Normal responses will now " + ("" if value == "true" else "not ") +
                                     "be in an embed")
        await ctx.send_error("Invalid config")

    @commands.command(brief="Lists current configs for the server.")
    async def configs(self, ctx: aoi.AoiContext):
        colors = await self.bot.db.guild_setting(ctx.guild.id)
        gain = await self.bot.db.get_currency_gain(ctx.guild)
        if colors.reply_embeds:
            await ctx.embed(
                title=f"{self.bot.user.name if self.bot.user else ''} Configs",
                fields=[
                    ("Embed Colors", f"ErrorColor: `{conversions.hex_color_to_string(colors.error_color)}`\n"
                                     f"InfoColor: `{conversions.hex_color_to_string(colors.info_color)}`\n"
                                     f"OKColor: `{conversions.hex_color_to_string(colors.ok_color)}`"),
                    ("Prefix", f"`{escape(self.bot.db.prefixes[ctx.guild.id], ctx)}`"),
                    ("Currency Gain", "Off" if not gain else f"{gain}/3m"),
                    ("Normal response embeds", "On" if colors.reply_embeds else "Off")
                ]
            )
        else:
            await ctx.send(f"__**{self.bot.user.name if self.bot.user else ''} Configs**__\n"
                           f"Embed Colors\n"
                           f"⋄ ErrorColor: `{conversions.hex_color_to_string(colors.error_color)}`\n"
                           f"⋄ InfoColor: `{conversions.hex_color_to_string(colors.info_color)}`\n"
                           f"⋄ OKColor: `{conversions.hex_color_to_string(colors.ok_color)}`\n"
                           f"Prefix: `{escape(self.bot.db.prefixes[ctx.guild.id], ctx)}`\n"
                           f"Currency Gain: {'Off' if not gain else str(gain) + '/3m'}\n"
                           f"Normal response embeds: {'On' if colors.reply_embeds else 'Off'}")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(GuildSettings(bot))
