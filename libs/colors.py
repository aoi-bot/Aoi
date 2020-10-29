import colorsys

from libs.converters import AoiColor


def rgb_gradient(color1: AoiColor, color2: AoiColor, num: int):
    rgb, rgb2 = color1.to_rgb(), color2.to_rgb()
    steps = [(rgb[x] - rgb2[x]) / (num - 1) for x in range(3)]
    return list(reversed([
        tuple(map(int, (rgb2[x] + steps[x] * n for x in range(3)))) for n in range(num + 1)
    ]))[1:]


def hls_gradient(color1: AoiColor, color2: AoiColor, num: int):
    hls, hls2 = color1.to_hls(), color2.to_hls()
    steps = [(hls[x] - hls2[x]) / (num - 1) for x in range(3)]
    colors = list(reversed([
        tuple(hls2[x] + steps[x] * n for x in range(3)) for n in range(num + 1)
    ]))[1:]
    return [tuple(int(channel * 256) for channel in colorsys.hls_to_rgb(*color)) for color in colors]
