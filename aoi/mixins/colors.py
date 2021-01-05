import io

from PIL import Image, ImageDraw

from libs.colors import rgb_gradient, hls_gradient
from libs.converters import AoiColor


class ColorCogMixin:
    def _gradient_buf(self, color1: AoiColor, color2: AoiColor, num: int, hls: bool):
        colors = hls_gradient(color1, color2, num) if hls else rgb_gradient(color1, color2, num)
        img = Image.new("RGB", (240, 48))
        img_draw = ImageDraw.Draw(img)
        for n, clr in enumerate(colors):
            img_draw.rectangle([
                (n * 240 / num, 0),
                ((n + 1) * 240 / num, 48)
            ], fill=tuple(map(int, clr)))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf, colors

    def _color_buf(self, color: AoiColor):
        img = Image.new("RGB", (120, 120), color.to_rgb())
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf
