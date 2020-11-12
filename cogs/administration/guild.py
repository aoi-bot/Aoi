from typing import Union

import aiohttp

import aoi
import discord
from discord.ext import commands


class Guilds(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands for managing servers"

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["guildnm", "servernm"],
                      brief="Renames the server")
    async def renameserver(self, ctx: aoi.AoiContext, *, name: str):
        await ctx.confirm_coro(f"Rename server to `{name}`?",
                               f"Server renamed to `{name}`",
                               "Server rename cancelled",
                               ctx.guild.edit(name=name))

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["guildav", "serverav", "servericon"],
                      brief="Sets the server's icon")
    async def serveravatar(self, ctx: aoi.AoiContext, *, url: str):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url) as resp:
                await ctx.confirm_coro("Change guild avatar?",
                                       "Avatar changed",
                                       "Avatar change cancelled",
                                       ctx.guild.edit(
                                           icon=await resp.content.read()
                                       ))

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["guildreg", "serverreg"],
                      brief="Sets the server's voice region")
    async def serverregion(self, ctx: aoi.AoiContext, *, region: str):
        region = region.lower().replace(" ", "-").replace("_", "-")
        if region not in map(str, discord.VoiceRegion):
            raise commands.BadArgument(f"Region `{region}` invalid. Do `{ctx.prefix}regions` "
                                       f"to view a list of supported regions")
        if "vip" in region and "VIP_REGIONS" not in ctx.guild.features:
            return await ctx.send_error(f"Region `{region}` is a VIP region and cannot be used for this server")
        reg = discord.VoiceRegion.try_value(region)
        await ctx.confirm_coro(f"Set server region to `{reg}`?",
                               f"Set to `{reg}`",
                               "Server region change cancelled",
                               ctx.guild.edit(region=reg))

    @commands.command(
        brief="List of regions the server can use"
    )
    async def regions(self, ctx: aoi.AoiContext):
        await ctx.send_info("Server regions:\n" +
                            "\n".join(f"◆ {x}" for x in filter(
                                lambda x: "vip" not in x or "VIP_REGIONS" in ctx.guild.features,
                                map(str, discord.VoiceRegion)
                            )),
                            title="Voice Regions")

    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_permissions(manage_emojis=True)
    @commands.command(
        brief="Deletes up to 10 emojis",
        aliases=["de"]
    )
    async def delemoji(self, ctx: aoi.AoiContext, emojis: commands.Greedy[Union[discord.Emoji, discord.PartialEmoji]]):
        e: discord.Emoji
        if len(emojis) < 1:
            raise commands.BadArgument("Must send an emoji")
        if len(emojis) > 10:
            raise commands.BadArgument("Must be less than 10 emojis")
        for e in emojis:
            if isinstance(e, discord.PartialEmoji) or e.guild_id != ctx.guild.id:
                return await ctx.send_error(f"{e} is not from this server. This command can only be used with emojis "
                                            f"that belong to this server.")

        async def _del():
            _e: discord.Emoji
            for _e in emojis:
                await _e.delete(reason=f"Bulk delete | {ctx.author} | {ctx.author.id}")

        await ctx.confirm_coro(
            "Delete " + " ".join(map(str, emojis)) + "?",
            "Emojis deleted",
            "Emoji deletion cancelled",
            _del()
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Guilds(bot))
