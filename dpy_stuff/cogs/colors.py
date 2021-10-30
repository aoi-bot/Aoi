import colorsys
import io
import random
from typing import List, Optional, Union

import discord
from discord.ext import commands
from discord.ext.commands import Greedy
from PIL import Image, ImageDraw
from PIL.ImageOps import colorize, grayscale

import bot
from dpy_stuff.cog_helpers.colors import ColorService
from libs.converters import AoiColor, FuzzyAoiColor


class Colors(commands.Cog, ColorService):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot
        super(Colors, self).__init__()

    @property
    def description(self):
        return "Commands to do with color"

    @commands.command(brief="Shows a color")
    async def color(self, ctx: bot.AoiContext, *, color: AoiColor):
        await ctx.embed(title=str(color), image=self._color_buf(color))

    @commands.command(brief="Shows a color palette", usage="color1 color2 ...")
    async def colors(self, ctx: bot.AoiContext, clrs: Greedy[FuzzyAoiColor]):
        valid_colors = [color for color in clrs if not color.attempt]
        invalid_colors = [color.attempt for color in clrs if color.attempt]
        if not valid_colors and invalid_colors:
            return await ctx.embed(
                title="Color Palette",
                description="Unknown Colors: " + ", ".join(invalid_colors),
            )
        clrs = valid_colors
        if not valid_colors:
            return
        img = Image.new("RGB", (120 * len(clrs), 120))
        img_draw = ImageDraw.Draw(img)
        for n, color in enumerate(clrs):
            img_draw.rectangle(
                [(n * 120, 0), (n * 120 + 120, 120)], fill=color.to_rgb()
            )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(
            title="Color Palette",
            image=buf,
            description=" ".join(
                "#" + "".join(hex(x)[2:].rjust(2, "0") for x in c.to_rgb())
                for c in clrs
            )
            + (  # noqa
                "\nUnknown Colors: " + ", ".join(invalid_colors)
                if invalid_colors
                else ""
            ),
        )

    @commands.command(
        brief="Shows a random color palette, sort by hue, random, or brightness",
        aliases=["rancolor", "ranclr"],
        description="""
                      randomcolors 15 hue
                      randomcolors brightness
                      """,
    )
    async def randomcolors(
        self,
        ctx: bot.AoiContext,
        number_of_colors: Optional[int] = 4,
        sort_by: str = "hue",
    ):
        clrs: List[discord.Colour] = []
        if number_of_colors > 250 or number_of_colors < 2:
            raise commands.BadArgument("Number of colors must be 2-250")
        for i in range(number_of_colors):
            clrs.append(
                discord.Colour(
                    random.randint(0, 0xFF) * 0x10000
                    + random.randint(0, 0xFF) * 0x100
                    + random.randint(0, 0xFF)
                )
            )
        if sort_by == "hue":
            clrs.sort(key=lambda x: colorsys.rgb_to_hsv(*x.to_rgb())[0])
        if sort_by in ("brightness", "bright"):
            clrs.sort(key=lambda x: colorsys.rgb_to_hls(*x.to_rgb())[1])
        rows = number_of_colors // 10 + 1
        cols = 10 if rows > 1 else number_of_colors
        if not number_of_colors % 10:
            rows -= 1
        img = Image.new("RGB", (120 * cols, rows * 120))
        img_draw = ImageDraw.Draw(img)
        for n, color in enumerate(clrs):
            row = n // 10
            col = n % 10
            img_draw.rectangle(
                [(col * 120, row * 120), (col * 120 + 120, row * 120 + 120)],
                fill=color.to_rgb(),
            )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        await ctx.embed(
            title="Color Palette",
            description=" ".join(map(str, clrs[:50]))
            + ("..." if len(clrs) >= 50 else ""),
            image=buf,
        )

    @commands.command(
        brief="Makes an RGB gradient between colors. Number of colors is optional, defaults to 4 and must be "
        "between 3 and 60.",
        aliases=["grad"],
        flags={"rgb": (None, "Make an RGB gradient instead")},
        description="""
        gradient red green 5
        gradient red green --rgb
        gradient red green 6 --rgb
        """,
    )
    async def gradient(
        self,
        ctx: bot.AoiContext,
        color1: AoiColor,
        color2: AoiColor,
        number_of_colors: Optional[int] = 4,
    ):
        buf, colors = self._gradient_buf(
            color1, color2, number_of_colors, "rgb" not in ctx.flags
        )
        await ctx.embed(
            title="Gradient",
            description=" ".join(
                "#" + "".join(hex(x)[2:].rjust(2, "0") for x in c) for c in colors
            ),
            image=buf,
        )

    @commands.max_concurrency(1, commands.BucketType.user)
    @commands.command(
        brief="Shows the adaptive color palette for an image. 2-10 colors, defaults to 6. The image must be attached "
        "with the command as a file"
    )
    async def adaptive(self, ctx: bot.AoiContext, number_of_colors: int = 6):
        if not ctx.message.attachments or len(ctx.message.attachments) == 0:
            return await ctx.send_error(
                "I need an image! Attach it with your command as a file."
            )
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error(
                "Invalid image type. Give me a jpg, jpeg, or png"
            )
        if not (2 <= number_of_colors <= 12):
            return await ctx.send_error(
                "Number of colors must be between 2 and 10, inclusive"
            )
        buf = io.BytesIO()
        buf.seek(0)
        await ctx.trigger_typing()
        await attachment.save(buf)
        im: Image = Image.open(buf).convert("RGB")
        paletted: Image = im.convert(
            "P", palette=Image.ADAPTIVE, colors=number_of_colors
        )
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
    @commands.command(
        brief="Split-tones an image. The image must be passed as an attachment"
    )
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
            return await ctx.send_error(
                "I need an image! Attach it with your command as a file."
            )
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error(
                "Invalid image type. Give me a jpg, jpeg, or png"
            )
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
    @commands.command(
        brief="Shows an image histogram. You must attach the image as an attachment"
    )
    async def histogram(self, ctx: bot.AoiContext):
        if not ctx.message.attachments or len(ctx.message.attachments) == 0:
            return await ctx.send_error(
                "I need an image! Attach it with your command as a file."
            )
        attachment: discord.Attachment = ctx.message.attachments[0]
        if not self._is_image(attachment.filename):
            return await ctx.send_error(
                "Invalid image type. Give me a jpg, jpeg, or png"
            )
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
