import io
import os
from typing import Optional, Union, List

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps
import ksoftapi
from PIL import Image, ImageDraw
from ksoftapi.models import LyricResult

import aoi
import discord
from discord.ext import commands
from libs.minesweeper import SpoilerMinesweeper, MinesweeperError
from libs.misc import arg_or_0_index


def _font(size: int) -> PIL.ImageFont.ImageFont:
    return PIL.ImageFont.truetype(
        "assets/merged.ttf", size=size)


class Fun(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.simp_fp = open("assets/simp-template.png", "rb")
        self.simp_img = PIL.Image.open(self.simp_fp)
        self.font = _font(33)
        self.av_mask = PIL.Image.new("L", self.simp_img.size, 0)
        self.av_mask_draw = PIL.ImageDraw.Draw(self.av_mask)
        self.av_mask_draw.ellipse((430, 384, 430 + 83, 384 + 83), fill=255)
        self._frames = []
        self._reload_frames()

    @property
    def description(self) -> str:
        return "Fun! :D"

    @commands.command(brief="Makes a discord minesweeper game",
                      flags={"raw": (None, "Show raw text"),
                             "no-spoiler": (None, "Don't include spoilers")})
    async def minesweeper(self, ctx: aoi.AoiContext, height: Optional[int] = 10,
                          width: Optional[int] = 10, bombs: Optional[int] = 10):
        flags = ctx.flags
        fmt = "```%s```" if "raw" in flags else "%s"
        try:
            await ctx.send(fmt % SpoilerMinesweeper(height, width, bombs).discord_str("no-spoiler" not in flags))
        except MinesweeperError as e:
            await ctx.send_error(str(e))

    @commands.command(brief="Hehe simp")
    async def simp(self, ctx: aoi.AoiContext, member: discord.Member = None):
        await ctx.trigger_typing()
        member = member or ctx.author
        # bounds = (496, 145, 679, 178)
        bounds = (490, 145, 685, 178)
        target_width = bounds[2] - bounds[0]
        img_copy: PIL.Image = self.simp_img.copy().convert("RGBA")

        draw = PIL.ImageDraw.Draw(img_copy)
        # draw.rectangle(bounds, fill=(0, 200, 0))
        name_size, name_height = draw.textsize(member.name, font=self.font)
        sz = 33
        font = self.font
        while name_size > target_width and sz > 4:
            sz -= 1
            font = _font(sz)
            name_size, name_height = draw.textsize(member.name, font=font)
        draw.text((587 - name_size / 2, 162 - name_height / 2), text=member.name, font=font,
                  fill=(0, 0, 0))

        av_url = member.avatar_url_as(format="png", size=128)
        av_buf = io.BytesIO()
        await av_url.save(av_buf)
        av_buf.seek(0)
        av_img = PIL.Image.open(av_buf).convert("RGBA")
        av_img = av_img.resize((83, 83))

        av_fg_img = PIL.Image.new("RGBA", self.simp_img.size)
        av_fg_img.paste(av_img, (430, 384))
        av_fg_img.putalpha(self.av_mask)

        img_copy = PIL.Image.alpha_composite(img_copy, av_fg_img)

        buf = io.BytesIO()
        img_copy.save(buf, "png")
        await ctx.embed(image=buf)

    @commands.command(
        brief="Shows the list of frames"
    )
    async def frames(self, ctx: aoi.AoiContext):
        await ctx.paginate(self._frames, 20, "Frames list", numbered=True, num_start=1)

    @commands.is_owner()
    @commands.command(
        brief="Reload frames"
    )
    async def reloadframes(self, ctx: aoi.AoiContext):
        _frames = [f for f in self._frames]
        try:
            self._reload_frames()
        except:  # noqa: E722
            await ctx.send_error("An error occurred while reloading the filers.")
            self._frames = [f for f in _frames]
            raise
        await ctx.send_ok("Frames reloaded")

    @commands.command(
        brief="Apply a frame around your avatar"
    )
    async def frame(self, ctx: aoi.AoiContext, frame_name: Union[int, str], member: discord.Member = None):
        member = member or ctx.author
        if (isinstance(frame_name, str) and frame_name not in self._frames) or \
                (isinstance(frame_name, int) and frame_name < 1 or frame_name > len(self._frames)):
            return await ctx.send_error(f"{frame_name} not a valid frame. Do `{ctx.prefix}frames` to see "
                                        f"the list of frames.")
        if isinstance(frame_name, int):
            frame_name = self._frames[frame_name - 1]
        frame_img = Image.open(f"assets/frames/{frame_name}.png").convert("RGBA")
        avatar_img_asset: discord.Asset = member.avatar_url_as(format="png", size=512)
        avatar_buf = io.BytesIO()
        await avatar_img_asset.save(avatar_buf)
        avatar_buf.seek(0)
        avatar_img = Image.open(avatar_buf).convert("RGBA").resize((512, 512))
        result_img = Image.alpha_composite(avatar_img, frame_img)
        mask = Image.new("L", (512, 512), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 512, 512), fill=255)
        result_img.putalpha(mask)
        result_buf = io.BytesIO()
        result_img.save(result_buf, "png")
        result_buf.seek(0)
        await ctx.embed(image=result_buf)

    def _reload_frames(self):
        self.bot.logger.info("frames:Loading frames")
        self._frames = [image.split(".")[0] for image in os.listdir("assets/frames/") if image.endswith(".png")]
        self.bot.logger.info(", ".join(self._frames))
        self.bot.logger.info("frames:Loaded frames")

    @commands.command(brief="Look up the lyrics for a song")
    async def lyrics(self, ctx: aoi.AoiContext, *, query: str):
        try:
            lyrs: List[LyricResult] = sorted(await self.bot.ksoft.music.lyrics(query),
                                             key=lambda x: -x.search_score)
        except ksoftapi.NoResults:
            return await ctx.send_error("No results found.")

        if len(lyrs) > 1:
            await ctx.send_ok(f"\n" + "\n".join(
                f"{n + 1} - {res.name} - {res.artist}"
                for n, res in enumerate(lyrs[:10])
            ))
            n = await ctx.input(int, ch=lambda x: 1 <= x <= min(10, len(lyrs))) - 1
            if n is None:
                return
            lyr = lyrs[n]
        else:
            lyr = lyrs[0]

        lines = [line.strip() for line in lyr.lyrics.split("\n")]
        pages = [""]
        for line in lines:
            if len(pages[-1]) + len(line) > 1000:
                pages.append(line)
            else:
                pages[-1] += f"\n{line}"
        await ctx.page_predefined(
            *[
                 discord.Embed(title=f"{lyr.name} -- {lyr.artist}", description=page)
                     .set_footer(text="Powered by KSoft")  # noqa
                     .set_thumbnail(url=lyr.album_art)
                 for page in pages
             ] + [
                 discord.Embed(title=f"{lyr.name} -- {lyr.artist}",
                               description=f"Song: {lyr.name}\n"
                                           f"Artist: {lyr.artist}\n"
                                           f"Album: {lyr.album}\n"
                                           f"Released in {arg_or_0_index(lyr.album_year)}\n"
                               )
                     .set_footer(text="Powered by KSoft")  # noqa
                     .set_thumbnail(url=lyr.album_art)
             ]
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Fun(bot))
