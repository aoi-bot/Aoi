import colorsys
import io
import random
from typing import List, Optional, Union

import discord
from PIL import Image, ImageDraw
from PIL.ImageOps import grayscale, colorize
from discord.ext import commands

import aoi
from libs.converters import AoiColor


class Colors(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to do with color"

    @commands.command(brief="Shows a color")
    async def color(self, ctx: aoi.AoiContext, *, color: AoiColor):
        img = Image.new("RGB", (120, 120), color.to_rgb())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(title=str(color),
                        image=buf)

    @commands.command(brief="Shows a color palette")
    async def colors(self, ctx: aoi.AoiContext, *, colors: str):
        replacements = {
            "yellow": "gold",
            "black": "000000"
        }
        mods = ""
        clrs: List[discord.Colour] = []
        colors = colors.split()
        conv = commands.ColourConverter()
        for i in colors:
            if i in ("darker", "dark", "light", "lighter"):
                mods = i
                continue
            if i in replacements:
                i = replacements[i]
            clrs.append(await conv.convert(ctx, f"{mods} {i}".strip()))
            mods = ""
        img = Image.new("RGB", (120 * len(clrs), 120))
        img_draw = ImageDraw.Draw(img)
        for n, color in enumerate(clrs):
            img_draw.rectangle([
                (n * 120, 0),
                (n * 120 + 120, 120)
            ], fill=color.to_rgb())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(title="Color Palette",
                        image=buf)

    @commands.command(brief="Shows a random color palette, sort by hue, random, or brightness",
                      aliases=["rancolor", "ranclr"])
    async def randomcolors(self, ctx: aoi.AoiContext, num: Optional[int] = 4, sort: str = "hue"):
        clrs: List[discord.Colour] = []
        if num > 250 or num < 2:
            raise commands.BadArgument("Number of colors must be 2-250")
        for i in range(num):
            clrs.append(discord.Colour(
                random.randint(0, 0xff) * 0x10000 +
                random.randint(0, 0xff) * 0x100 +
                random.randint(0, 0xff)
            ))
        if sort == "hue":
            clrs.sort(key=lambda x: colorsys.rgb_to_hsv(*x.to_rgb())[0])
        if sort in ("brightness", "bright"):
            clrs.sort(key=lambda x: colorsys.rgb_to_hls(*x.to_rgb())[1])
        rows = num // 10 + 1
        cols = 10 if rows > 1 else num
        if not num % 10:
            rows -= 1
        img = Image.new("RGB", (120 * cols, rows * 120))
        img_draw = ImageDraw.Draw(img)
        for n, color in enumerate(clrs):
            row = n // 10
            col = n % 10
            img_draw.rectangle([
                (col * 120, row * 120),
                (col * 120 + 120, row * 120 + 120)
            ], fill=color.to_rgb())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(title="Color Palette",
                        description=" ".join(map(str, clrs[:50])) +
                                    ("..." if len(clrs) >= 50 else ""),
                        image=buf)

    @commands.command(
        brief="Makes an RGB gradient between colors. Number of colors is optional, defaults to 4 and must be "
              "between 3 and 10."
    )
    async def gradient(self, ctx: aoi.AoiContext, color1: discord.Colour, color2: discord.Colour, num: int = 4):
        if num < 3 or num > 10:
            return await ctx.send_error("Number of colors must be between 2 and 10")
        rgb, rgb2 = color1.to_rgb(), color2.to_rgb()
        steps = [(rgb[x] - rgb2[x]) / (num - 1) for x in range(3)]
        colors = list(reversed([tuple(map(int, (rgb2[x] + steps[x] * n for x in range(3)))) for n in range(num + 1)]))
        img = Image.new("RGB", (240, 48))
        img_draw = ImageDraw.Draw(img)
        for n, clr in enumerate(colors):
            img_draw.rectangle([
                (n * 240 / num, 0),
                ((n + 1) * 240 / num, 48)
            ], fill=tuple(map(int, clr)))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(title="Gradient",
                        description=" ".join("#" + "".join(hex(x)[2:] for x in c) for c in colors[1:]),
                        image=buf)

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        brief="Shows the adaptive color palette for an image. 2-10 colors, defaults to 6."
    )
    async def adaptive(self, ctx: aoi.AoiContext, num_colors: int = 6):
        if not ctx.message.attachments or len(ctx.message.attachments) == 0:
            return await ctx.send_error("I need an image! Attach it with your command as a file.")
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error("Invalid image type. Give me a jpg, jpeg, or png")
        if not (2 <= num_colors <= 12):
            return await ctx.send_error("Number of colors must be between 2 and 10, inclusive")
        buf = io.BytesIO()
        buf.seek(0)
        await ctx.trigger_typing()
        await attachment.save(buf)
        im: Image = Image.open(buf).convert("RGB")
        paletted: Image = im.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
        palette = paletted.getpalette()
        color_counts = sorted(paletted.getcolors(), reverse=True)
        colors = list()
        for i in range(num_colors):
            palette_index = color_counts[i][1]
            dominant_color = palette[palette_index * 3:palette_index * 3 + 3]
            colors.append(tuple(dominant_color))
        colors.sort(key=lambda x: colorsys.rgb_to_hsv(*x)[0])
        im = im.resize((60 * num_colors, int(60 * num_colors * im.size[1] / im.size[0])), Image.ANTIALIAS)

        palette = Image.new('RGB', (60 * num_colors, 60 + im.size[1]))
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
            image=buf
        )

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        brief="Split-tones an image"
    )
    async def duotone(self, ctx: aoi.AoiContext, black: discord.Colour, white: discord.Colour,
                      mid: Union[discord.Colour, str] = None, black_point: int = 0, white_point: int = 255,
                      mid_point: int = 127):
        if isinstance(mid, str):
            if mid.lower() == "none":
                mid = None
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
        duo = colorize(gs, black.to_rgb(), white.to_rgb(), mid.to_rgb() if mid else None,
                       black_point, white_point, mid_point)
        duo = Image.composite(duo, Image.new("RGB", duo.size, (0x00, 0x00, 0x00)), gs)
        buf.close()
        buf = io.BytesIO()
        duo.save(buf, "PNG")
        await ctx.embed(
            image=buf
        )

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        brief="Shows an image histogram"
    )
    async def histogram(self, ctx: aoi.AoiContext):
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
                rgb_draws[j].rectangle((i + 12, 140, i + 12, 140 - rgb[j][i]), 0xff)

        histogram = Image.merge("RGB", rgb_images)
        hist_draw = ImageDraw.Draw(histogram)

        hist_draw.line([12, 12, 12, 140, 268, 140], 0xffffff)
        for r in range(12, 141, 16):
            hist_draw.line([8, r, 12, r], 0xffffff)
        for r in range(12, 269, 32):
            hist_draw.line([r, 140, r, 144], 0xffffff)

        buf.close()
        buf = io.BytesIO()
        histogram.save(buf, "PNG")
        await ctx.embed(
            image=buf
        )

    def _is_image(self, name: str) -> bool:
        return any(name.endswith(f".{x}") for x in "jpg,jpeg,png".split(","))


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Colors(bot))
