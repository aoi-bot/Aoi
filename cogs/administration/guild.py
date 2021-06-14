import io
from typing import Union, Optional

import aiohttp
from PIL import Image
from aiohttp import ClientResponseError
from aiohttp.http_exceptions import BadHttpMessage

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
                      brief="Sets the server's icon, or show the current.")
    async def serveravatar(self, ctx: aoi.AoiContext, *, url: str = None):
        if not url:
            return await ctx.send(ctx.guild.icon.url if ctx.guild.icon else "No server icon set")
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
                      brief="Sets the server's voice region",
                      description="""
                      serverregion us east
                      serverregion us-east
                      """)
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

    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.command(aliases=["voicereg", "vcreg"],
                      brief="Sets a voice channel's region. Defaults to the voice channel you're in",
                      description="""
                      vcregion us-east
                      vcregion 128312312313 us-east
                      vcregion "General VC" us-east
                      """)
    async def vcregion(self, ctx: aoi.AoiContext, channel: Optional[discord.VoiceChannel], *, region: str):
        if not channel:
            if ctx.author.voice:
                voice_state: discord.VoiceState = ctx.author.voice
                if voice_state.channel:
                    channel = voice_state.channel
                else:
                    return await ctx.send_error("Join a voice channel or add a voice channel ID to the command")
        if region not in map(str, discord.VoiceRegion):
            raise commands.BadArgument(f"Region `{region}` invalid. Do `{ctx.prefix}regions` "
                                       f"to view a list of supported regions")
        if "vip" in region and "VIP_REGIONS" not in ctx.guild.features:
            return await ctx.send_error(f"Region `{region}` is a VIP region and cannot be used for this server")
        reg = discord.VoiceRegion.try_value(region)
        await ctx.confirm_coro(f"Set {channel.name} region to `{reg}`?",
                               f"Set to `{reg}`",
                               "Channel region change cancelled",
                               channel.edit(rtc_region=reg))

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
        aliases=["de"],
        usage="emoji1 emoji2 ..."
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

    @commands.bot_has_permissions(manage_emojis=True)
    @commands.has_permissions(manage_emojis=True)
    @commands.command(
        brief="Adds an emoji",
        aliases=["ae"],
        description="""
        addemoji emoji_name :emoji:
        addemoji emoji_name emoji.com/my_awesome_emoji.png
        """
    )
    async def addemoji(self, ctx: aoi.AoiContext, name: str, src: Union[discord.PartialEmoji, str]):  # noqa c901
        if len(name) > 32 or len(name) < 2:
            raise commands.BadArgument("Emoji name must be 2-32 characters")
        if isinstance(src, discord.PartialEmoji):
            if src.is_unicode_emoji():
                return await ctx.send_error("Must be a custom emoji")
            src = str(src.url)
        buf = io.BytesIO()
        async with aiohttp.ClientSession() as sess:
            try:
                async with sess.get(src) as resp:
                    if resp.status != 200:
                        return await ctx.send_error(f"Server responded with a {resp.status}")
                    if "Content-Type" in resp.headers:
                        typ = resp.headers["Content-Type"].split("/")[-1]
                    if "Content-Type" not in resp.headers or resp.headers["Content-Type"] not in \
                            ("image/gif", "image/jpeg", "image/png"):
                        return await ctx.send_error(f"That doesn't seem to be an image")
                    buf.write(await resp.content.read())
            except (ClientResponseError, BadHttpMessage):
                await ctx.send_error(f"I got an error trying to get that image."
                                     f"Try pasting the image into discord and using that link instead.")
                raise
        buf.seek(0)
        ratio = 0
        total_ratio = 1
        while buf.__sizeof__() > 255000 and typ != "gif":
            # try to resize image to emoji size
            ratio = 255000 / buf.__sizeof__()
            total_ratio *= ratio
            image: Image.Image = Image.open(buf)
            image.load()
            current_size = image.size
            image = image.resize((int(current_size[0] * ratio), int(current_size[1] * ratio)))
            buf2 = io.BytesIO()
            image.save(buf2, format='PNG')
            print(buf2.__sizeof__())
            buf = buf2
            buf.seek(0)
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=buf.read())
        except discord.HTTPException as e:
            return await ctx.send_error(str(e))
        await ctx.send_ok(f"Added {emoji} {emoji.name}." +
                          (f" Image was scaled down to 1/{round(1 / total_ratio, 1)} its size to make it "
                           f"small enough for an emoji"
                           if ratio else ""))


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Guilds(bot))
