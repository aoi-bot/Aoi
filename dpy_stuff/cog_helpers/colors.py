import colorsys
import io

from discord.ext import commands
from PIL import Image, ImageDraw

from libs.converters import AoiColor


# noinspection PyMethodMayBeStatic
class ColorService:
    def __init__(self):
        self.MAX = 60

    def _gradient_buf(self, color1: AoiColor, color2: AoiColor, num: int, hls: bool):
        if num < 3 or num > self.MAX:
            raise commands.BadArgument(
                f"Number of colors must be between 2 and {self.MAX}"
            )
        colors = (
            self.hls_gradient(color1, color2, num)
            if hls
            else self.rgb_gradient(color1, color2, num)
        )
        img = Image.new("RGB", (240, 48))
        img_draw = ImageDraw.Draw(img)
        for n, clr in enumerate(colors):
            img_draw.rectangle(
                [(n * 240 / num, 0), ((n + 1) * 240 / num, 48)],
                fill=tuple(map(int, clr)),
            )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf, colors

    def _color_buf(self, color: AoiColor):
        img = Image.new("RGB", (120, 120), color.to_rgb())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf

    def rgb_gradient(self, color1: AoiColor, color2: AoiColor, num: int):
        rgb, rgb2 = color1.to_rgb(), color2.to_rgb()
        steps = [(rgb[x] - rgb2[x]) / (num - 1) for x in range(3)]
        return list(
            reversed(
                [
                    tuple(map(int, (rgb2[x] + steps[x] * n for x in range(3))))
                    for n in range(num + 1)
                ]
            )
        )[1:]

    def hls_gradient(self, color1: AoiColor, color2: AoiColor, num: int):
        hls, hls2 = color1.to_hls(), color2.to_hls()
        steps = [(hls[x] - hls2[x]) / (num - 1) for x in range(3)]
        colors = list(
            reversed(
                [
                    tuple(hls2[x] + steps[x] * n for x in range(3))
                    for n in range(num + 1)
                ]
            )
        )[1:]
        return [
            tuple(int(channel * 256) for channel in colorsys.hls_to_rgb(*color))
            for color in colors
        ]
