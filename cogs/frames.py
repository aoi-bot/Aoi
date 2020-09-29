import io
import logging
import os
from typing import Union

import discord
from PIL import Image, ImageDraw
from discord.ext import commands

import aoi


class Frames(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self._frames = []
        self._reload_frames()

    @property
    def description(self) -> str:
        return "Put cute frames around your avatar"

    def _reload_frames(self):
        logging.info("frames:Loading frames")
        self._frames = [image.split(".")[0] for image in os.listdir("assets/frames/") if image.endswith(".png")]
        logging.info(", ".join(self._frames))
        logging.info("frames:Loaded frames")

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
        except:
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
            frame_name = self._frames[frame_name-1]
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


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Frames(bot))
