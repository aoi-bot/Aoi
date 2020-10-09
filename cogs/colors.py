import colorsys
import io
import random
from typing import List, Optional

import discord
from PIL import Image, ImageDraw
from discord.ext import commands

import aoi


class Colors(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Commands to do with color"

    @commands.command(brief="Shows a color")
    async def color(self, ctx: aoi.AoiContext, *, color: discord.Colour):
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

    @commands.command(
        brief="Shows the adaptive color palette for an image. 2-12 colors, defaults to 6."
    )
    async def adaptive(self, ctx: aoi.AoiContext, colors: int = 6):
        pass


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Colors(bot))
