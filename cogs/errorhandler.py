import sys
import traceback

import discord
from discord.ext import commands
import aoi


class ErrorHandler(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: aoi.AoiContext, error):
        if hasattr(ctx.command, 'on_error'):
            return
        cog: commands.Cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return
        ignored = (commands.CommandNotFound, )

        error = getattr(error, 'original', error)
        
        if isinstance(error, ignored):
            return
        if isinstance(error, commands.DisabledCommand):
            await ctx.send_error(f'{ctx.command} has been disabled.')
        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, aoi.RoleError):
            await ctx.send_error(str(error))
        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(ErrorHandler(bot))
