import colorsys
import io
import random
from typing import List, Optional, Union

import discord
from discord.ext import commands
from discord.ext.commands import Greedy
from PIL import Image, ImageDraw
from PIL.ImageOps import colorize, grayscale

from aoi import bot
from dpy_stuff.cog_helpers.colors import ColorService
from aoi.libs.converters import AoiColor, FuzzyAoiColor


class Colors(commands.Cog, ColorService):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot
        super(Colors, self).__init__()

    @property
    def description(self):
        return "Commands to do with color"

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        brief="Shows the adaptive color palette for an image. 2-10 colors, defaults to 6. The image must be attached "
        "with the command as a file"
    )
    async def adaptive(self, ctx: bot.AoiContext, number_of_colors: int = 6):
        if not ctx.message.attachments or len(ctx.message.attachments) == 0:
            return await ctx.send_error("I need an image! Attach it with your command as a file.")
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error("Invalid image type. Give me a jpg, jpeg, or png")
        if not (2 <= number_of_colors <= 12):
            return await ctx.send_error("Number of colors must be between 2 and 10, inclusive")
        buf = io.BytesIO()
        buf.seek(0)
        await ctx.trigger_typing()
        await attachment.save(buf)
        im: Image = Image.open(buf).convert("RGB")
        paletted: Image = im.convert("P", palette=Image.ADAPTIVE, colors=number_of_colors)
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        colors = list()
        for i in range(number_of_colors):
            palette_index = color_counts[i][1]
            dominant_color = palette[palette_index * 3 : palette_index * 3 + 3]
            colors.append(tuple(dominant_color))
        colors.sort(key=lambda x: colorsys.rgb_to_hsv(*x)[0])
        im = im.resize(
            (
                60 * number_of_colors,
                int(60 * number_of_colors * im.size[1] / im.size[0]),
            ),
            Image.ANTIALIAS,
        )

        palette = Image.new("RGB", (60 * number_of_colors, 60 + im.size[1]))
        palette.paste(im, (0, 60))
        draw = ImageDraw.Draw(palette)

        pos_x = 0
        for color in colors:
            draw.rectangle([pos_x, 0, pos_x + 60, 60], fill=color)
            pos_x += 60

        buf.close()
        buf = io.BytesIO()
        palette.save(buf, "PNG")

        await ctx.embed(
            description=" ".join("#" + "".join(hex(x)[2:] for x in c) for c in colors),
            image=buf,
        )

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(brief="Split-tones an image. The image must be passed as an attachment")
    async def duotone(
        self,
        ctx: bot.AoiContext,
        dark_color: AoiColor,
        light_color: AoiColor,
        midpoint_color: Union[AoiColor, str] = None,
        black_point: int = 0,
        white_point: int = 255,
        mid_point: int = 127,
    ):
        if isinstance(midpoint_color, str):
            if midpoint_color.lower() == "none":
                midpoint_color = None
            else:
                raise commands.BadArgument("mid must be a color or None")
        if not ctx.message.attachments or len(ctx.message.attachments) == 0:
            return await ctx.send_error("I need an image! Attach it with your command as a file.")
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error("Invalid image type. Give me a jpg, jpeg, or png")
        buf = io.BytesIO()
        buf.seek(0)
        await ctx.trigger_typing()
        await attachment.save(buf)
        im: Image = Image.open(buf).convert("RGB")
        gs = grayscale(im)
        duo = colorize(
            gs,
            dark_color.to_rgb(),
            light_color.to_rgb(),
            midpoint_color.to_rgb() if midpoint_color else None,
            black_point,
            white_point,
            mid_point,
        )
        duo = Image.composite(duo, Image.new("RGB", duo.size, (0x00, 0x00, 0x00)), gs)
        buf.close()
        buf = io.BytesIO()
        duo.save(buf, "PNG")
        await ctx.embed(image=buf)

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(brief="Shows an image histogram. You must attach the image as an attachment")
    async def histogram(self, ctx: bot.AoiContext):
        if not ctx.message.attachments or len(ctx.message.attachments) == 0:
            return await ctx.send_error("I need an image! Attach it with your command as a file.")
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error("Invalid image type. Give me a jpg, jpeg, or png")
        buf = io.BytesIO()
        buf.seek(0)
        await ctx.trigger_typing()
        await attachment.save(buf)
        im: Image = Image.open(buf).convert("RGB")
        hist: List[int] = im.histogram()
        max_rgb = max(hist)
        hist = [int(x / max_rgb * 128) for x in hist]
        rgb = hist[:256], hist[256:512], hist[512:]

        rgb_images = [Image.new("L", (280, 152), 0) for _ in rgb]
        rgb_draws = [ImageDraw.Draw(im) for im in rgb_images]

        for i in range(256):
            for j in range(3):
                rgb_draws[j].rectangle((i + 12, 140, i + 12, 140 - rgb[j][i]), 0xFF)

        histogram = Image.merge("RGB", rgb_images)
        hist_draw = ImageDraw.Draw(histogram)

        hist_draw.line([12, 12, 12, 140, 268, 140], 0xFFFFFF)
        for r in range(12, 141, 16):
            hist_draw.line([8, r, 12, r], 0xFFFFFF)
        for r in range(12, 269, 32):
            hist_draw.line([r, 140, r, 144], 0xFFFFFF)

        buf.close()
        buf = io.BytesIO()
        histogram.save(buf, "PNG")
        await ctx.embed(image=buf)

    def _is_image(self, name: str) -> bool:
        return any(name.endswith(f".{x}") for x in "jpg,jpeg,png".split(","))


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(Colors(bot))
