import discord
from discord.ext import commands
import aoi


class Roles(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @commands.has_permissions(manage_roles=True)
    @commands.command(brief="Toggles if a role is mentionable", aliases=["rolem", "mentionable"])
    async def rolementionable(self, ctx: aoi.AoiContext, *, role: discord.Role):
        if role >= ctx.author.top_role and ctx.guild.owner_id != ctx.author.id:
            raise commands.CommandError("Role to edit must be lower than your highest")
        if role >= ctx.me.top_role:
            raise commands.CommandError("I can't edit a role higher than mine")
        await role.edit(mentionable=not role.mentionable)
        await ctx.send_info(f"{role.mention} is now {'' if role.mentionable else 'un'}mentionable")



def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Roles(bot))
