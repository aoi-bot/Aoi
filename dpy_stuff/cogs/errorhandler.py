import sys
import traceback

import discord
from discord.ext import commands

from aoi import bot


def _(s: str):
    for k, v in {"colour": "color"}.items():
        s = (
            s.replace(k, v)
            .replace(k.title(), v.title())
            .replace(k.lower(), v.lower())
            .replace(k.upper(), v.upper())
        )
    return s


class ErrorHandler(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: bot.AoiContext, error):  # noqa: C901
        if hasattr(ctx.command, "on_error"):
            return
        cog: commands.Cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return
        ignored = (commands.CommandNotFound,)

        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return
        if isinstance(error, commands.NSFWChannelRequired):
            await ctx.send_error("This command can only be used in NSFW channels")
        if isinstance(error, commands.DisabledCommand):
            await ctx.send_error(f"{ctx.command} has been disabled.")
        elif isinstance(
            error,
            (
                commands.NotOwner,
                commands.MissingPermissions,
                commands.BotMissingAnyRole,
                commands.MissingRole,
                commands.BotMissingPermissions,
            ),
        ):
            await ctx.send_error(_(str(error)))
        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(
                    f"{ctx.command} can not be used in Private Messages."
                )
            except discord.HTTPException:
                pass
        elif isinstance(error, bot.CurrencyError):
            await ctx.send_error(
                f"You must have ${error.amount_needed} ({'global' if error.is_global else 'server'}), "
                f"and you have {error.amount_has}."
            )
        elif isinstance(error, bot.RoleHierarchyError):
            await ctx.send_error(_(str(error)))
        elif isinstance(error, bot.PermissionFailed):
            if (await self.bot.db.guild_setting(ctx.guild.id)).perm_errors:
                await ctx.send_error(str(error))
        elif isinstance(error, discord.Forbidden):
            await ctx.send_error("I don't have the permissions for that")
        elif isinstance(
            error, (commands.BadArgument, commands.MissingRequiredArgument)
        ):
            await ctx.send_error(_(str(error)))
        elif isinstance(error, bot.DomainError):
            await ctx.send_error(
                f"Domain Error - the value supplied was outside of the "
                f"valid input range of `{error.token}`"
            )
        elif isinstance(error, bot.CalculationSyntaxError):
            await ctx.send_error(
                f"Syntax Error - An error occured while parsing the expression"
            )
        elif isinstance(error, bot.MathError):
            await ctx.send_error(
                f"Math Error - An error occured while evaluating the expression"
            )
        elif isinstance(error, commands.errors.FlagError):
            await ctx.send_error(
                f"Flag `{error.attempted}` is an invalid flag and must be one of "
                + " ".join(f"`{flag}`" for flag in error.supported)
            )
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send_error(
                f"You are on cooldown. Try again in {round(error.retry_after)}s"
            )
        else:
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(ErrorHandler(bot))
