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
import io
import typing
from collections.abc import Sequence

import hikari
import PIL.Image
import PIL.ImageDraw
import tanjun

from aoi.libs.converters import FuzzyAoiColor


async def color_palette(
    ctx: typing.Union[tanjun.abc.MessageContext, tanjun.abc.SlashContext],
    colors: Sequence[FuzzyAoiColor],
):
    valid_colors = [color for color in colors if not color.attempt]
    invalid_colors = [color.attempt for color in colors if color.attempt]
    if not valid_colors and invalid_colors:
        return await ctx.respond(f"No valid colors were supplied")
    if not valid_colors:
        return
    img = PIL.Image.new("RGB", (120 * len(valid_colors), 120))
    img_draw = PIL.ImageDraw.Draw(img)
    for n, color in enumerate(valid_colors):
        img_draw.rectangle([(n * 120, 0), (n * 120 + 120, 120)], fill=color.to_rgb())
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    await ctx.respond(
        embed=hikari.Embed(
            title="Color palette",
            description=" ".join(
                "#" + "".join(hex(channel)[2:].rjust(2, "0") for channel in c.to_rgb())
                for c in valid_colors
            )
            + (
                "\nUnknown Colors: " + ", ".join(invalid_colors)
                if invalid_colors
                else ""
            ),
        ).set_image(buf)
    )
