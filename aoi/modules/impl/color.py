"""
Copyright 2021 crazygmr101

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the 
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit 
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the 
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE 
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR 
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import colorsys
import io
import random
from collections.abc import Sequence

import PIL.Image
import PIL.ImageDraw
import hikari

from aoi import AoiContextMixin
from aoi.bot import AoiDatabase
from aoi.bot.injected import EmbedCreator, ColorService
from aoi.libs.converters import FuzzyAoiColor, AoiColor


async def color_palette(
    ctx: AoiContextMixin,
    colors: Sequence[FuzzyAoiColor],
):
    valid_colors = [color for color in colors if not color.attempt]
    invalid_colors = [color.attempt for color in colors if color.attempt]
    if not valid_colors and invalid_colors:
        await ctx.get_builder().as_error().with_description("No valid colors were supplied").send()
        return
    if not valid_colors:
        return
    img = PIL.Image.new("RGB", (120 * len(valid_colors), 120))
    img_draw = PIL.ImageDraw.Draw(img)
    for n, color in enumerate(valid_colors):
        img_draw.rectangle([(n * 120, 0), (n * 120 + 120, 120)], fill=color.to_rgb())
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await ctx.get_builder().with_title("Color Palette").with_description(
        " ".join("#" + "".join(hex(channel)[2:].rjust(2, "0") for channel in c.to_rgb()) for c in valid_colors)
        + ("\nUnknown Colors: " + ", ".join(invalid_colors) if invalid_colors else "")
    ).with_image(buf).send()


async def random_colors(
    ctx: AoiContextMixin,
    number_of_colors: int,
    sort_by: str,
    _embed: EmbedCreator,
    _database: AoiDatabase,
):
    colors: list[hikari.Color] = []
    if number_of_colors > 250 or number_of_colors < 2:
        await ctx.get_builder().as_error().with_description(
            "Number of colors must be between 2 and 250, inclusive"
        ).send()
        return
    for i in range(number_of_colors):
        colors.append(
            hikari.Color.from_rgb(
                random.randint(0, 0xFF),
                random.randint(0, 0xFF),
                random.randint(0, 0xFF),
            )
        )
    if sort_by == "hue":
        colors.sort(key=lambda x: colorsys.rgb_to_hsv(*x.rgb)[0])
    if sort_by in ("brightness", "bright"):
        colors.sort(key=lambda x: colorsys.rgb_to_hls(*x.rgb)[1])
    rows = number_of_colors // 10 + 1
    cols = 10 if rows > 1 else number_of_colors
    if not number_of_colors % 10:
        rows -= 1
    img = PIL.Image.new("RGB", (120 * cols, rows * 120))
    img_draw = PIL.ImageDraw.Draw(img)
    for n, color in enumerate(colors):
        row = n // 10
        col = n % 10
        img_draw.rectangle(
            [(col * 120, row * 120), (col * 120 + 120, row * 120 + 120)],
            fill=color.rgb,
        )
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await ctx.get_builder().with_title("Color Palette").with_description(
        " ".join(map(str, colors[:50])) + ("..." if len(colors) >= 50 else "")
    ).with_image(buf).send()


async def gradient(
    ctx: AoiContextMixin,
    color1: AoiColor,
    color2: AoiColor,
    number_of_colors: int,
    rgb: bool,
    _database: AoiDatabase,
    _colors: ColorService,
):
    buf, colors = _colors.gradient_buffer(color1, color2, number_of_colors, not rgb)
    await ctx.get_builder().with_title("Gradient").with_description(
        " ".join("#" + "".join(hex(x)[2:].rjust(2, "0") for x in c) for c in colors)
    ).with_image(buf).send()
