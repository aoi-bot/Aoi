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
import typing

import PIL.Image
import PIL.ImageDraw

from aoi.libs.converters import AoiColor

ColorTuple = typing.TypeVar("ColorTuple", bound=tuple[int, int, int])


class ColorService:
    def __init__(self):
        self.MAX_COLORS = 60

    def gradient_buffer(
        self, color1: AoiColor, color2: AoiColor, number_of_colors: int, hls: bool
    ) -> tuple[io.BytesIO, list[ColorTuple]]:
        if number_of_colors < 3 or number_of_colors > self.MAX_COLORS:
            raise ValueError  # TODO custom exception?
        colors = (
            self.hls_gradient(color1, color2, number_of_colors)
            if hls
            else self.rgb_gradient(color1, color2, number_of_colors)
        )
        img = PIL.Image.new("RGB", (240, 48))
        img_draw = PIL.ImageDraw.Draw(img)
        for n, color in enumerate(colors):
            img_draw.rectangle(
                [
                    (n * 240 / number_of_colors, 0),
                    ((n + 1) * 240 / number_of_colors, 48),
                ],
                fill=tuple(map(int, color)),
            )
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf, colors

    @staticmethod
    def rgb_gradient(color1: AoiColor, color2: AoiColor, num: int) -> list[ColorTuple]:
        rgb, rgb2 = color1.to_rgb(), color2.to_rgb()
        steps = [(rgb[x] - rgb2[x]) / (num - 1) for x in range(3)]
        return list(
            reversed(
                [
                    typing.cast(
                        ColorTuple,
                        tuple(map(int, (rgb2[x] + steps[x] * n for x in range(3)))),
                    )
                    for n in range(num + 1)
                ]
            )
        )[1:]

    @staticmethod
    def hls_gradient(color1: AoiColor, color2: AoiColor, num: int) -> list[ColorTuple]:
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
            typing.cast(
                ColorTuple,
                tuple(int(channel * 256) for channel in colorsys.hls_to_rgb(*color)),
            )
            for color in colors
        ]

    def color_buf(self, color: AoiColor) -> io.BytesIO:
        img = PIL.Image.new("RGB", (120, 120), color.to_rgb())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf
