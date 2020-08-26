import io
import itertools
from typing import Dict, Any, Tuple, Union

import PIL
import PIL.Image as I
import PIL.ImageDraw as D
import PIL.ImageFont as F
import discord
from discord.ext import commands

import aoi

lvl_list = [0] + [8 * lvl + 40 for lvl in range(100000)]
ttl_lvl_list = list(itertools.accumulate(lvl_list))

print(lvl_list[:6])
print(ttl_lvl_list[:6])


def _xp_per_level(lvl: int):
    return lvl_list[lvl]


def _level(xp: int):
    for n, v in enumerate(ttl_lvl_list):
        if v > xp:
            return n - 1, lvl_list[n] - (v - xp)


def _center(x, y, x2, y2, w, h):
    return (x + x2) / 2 - w / 2, (y + y2) / 2 - h / 2


def _fit(w, h, text, size, draw, *, w_pad=5, h_pad=5):
    _w, _h = draw.textsize(text, font=_font(size))
    while ((_w > w - w_pad * 2) or (_h > h - h_pad * 2)) and size > 4:
        print(_w, w, w + w_pad * 2)
        size -= 1
        print(f"try {size}")
        _w, _h = draw.textsize(text, font=_font(size))
    return _w, _h, size


def _center_and_fit(x, y, x2, y2, text, size, draw, *, w_pad=5, h_pad=5):
    w, h, sz = _fit(abs(x - x2), abs(y - y2), text, size, draw, w_pad=w_pad, h_pad=h_pad)
    x, y = _center(x, y, x2, y2, w, h)
    return x, y, w, h, sz


def _font(size: int) -> PIL.ImageFont.ImageFont:
    return F.truetype(
        "assets/merged.ttf", size=size)


def _16(*args: Union[float, int]) -> [Union[float, int], ...]:
    return tuple(map(lambda x: 16 * x, args))


class Profile(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.fp = open("assets/profile.png", "rb")
        self.background: PIL.Image.Image = PIL.Image.open(self.fp)
        self.level_font: PIL.ImageFont.ImageFont = _font(42)

    @property
    def description(self):
        return "Edit/view profile cards"

    def _get_ranked(self, guild: int) -> Dict[int, int]:
        order = sorted(self.bot.db.xp[guild].items(), key=lambda x: x[1], reverse=True)
        return {o[0]: o[1] for o in order}

    def _get_rank(self, member: discord.Member) -> int:
        # only called in xp, so no need for ensure_xp_entry
        r = 0
        for k, v in self._get_ranked(member.guild.id).items():
            r += 1
            if k == member.id:
                return r

    def _get_global_rank(self, member: discord.Member) -> int:
        order = sorted(self.bot.db.global_xp.items(), key=lambda x: x[1], reverse=True)
        ordered = {o[0]: o[1] for o in order}
        r = 0
        for k, v in ordered.items():
            r += 1
            if k == member.id:
                return r

    @commands.command(
        brief="View someone's profile"
    )
    async def profile(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        global_xp = self.bot.db.global_xp[member.id]
        server_xp = self.bot.db.xp[ctx.guild.id][member.id]
        global_level, global_rem = _level(global_xp)
        server_level, server_rem = _level(server_xp)
        avatar_buf = io.BytesIO()
        await member.avatar_url_as(format="png").save(avatar_buf)
        avatar_buf.seek(0)
        img = self.background.copy()
        avatar_img = I.open(avatar_buf)
        avatar_img = avatar_img.resize((128, 128))
        img_draw = D.Draw(img)
        img.paste(avatar_img, (32, 32))
        avatar_buf.close()

        # create overlays for the xp bars
        global_width = 330.66672 * global_rem / _xp_per_level(global_level + 1)
        global_xp_poly = (133.33328, 192), \
                         (133.33328 + global_width, 192), \
                         (117.33328 + global_width, 240), \
                         (117.33328, 240)

        server_width = 330.66672 * server_rem / _xp_per_level(server_level + 1)
        server_xp_poly = (112, 256), \
                         (112 + server_width, 256), \
                         (96 + server_width, 304), \
                         (96, 304)
        overlay = I.new("RGBA", img.size, (0, 0, 0, 0))
        D.Draw(overlay).polygon(global_xp_poly, fill=(0, 0, 0) + (120,))
        D.Draw(overlay).polygon(server_xp_poly, fill=(0, 0, 0) + (120,))
        img = PIL.Image.alpha_composite(img, overlay)
        img_draw = D.Draw(img)

        # draw text
        x, y, _, _, sz = _center_and_fit(217.6, 80, 480, 32, member.name, 32, img_draw,
                                         w_pad=24)
        img_draw.text((x, y), member.name, font=_font(sz))

        x, y, _, _, sz = _center_and_fit(115.8, 191, 480, 242,
                                         f"Level {global_level} - # {self._get_global_rank(member)}",
                                         32, img_draw, w_pad=24)
        img_draw.text((x, y), f"Level {global_level} - # {self._get_global_rank(member)}",
                      font=_font(sz))

        x, y, _, _, sz = _center_and_fit(95, 255, 459.2, 306,
                                         f"Level {server_level} - # {self._get_rank(member)}",
                                         32, img_draw, w_pad=24)
        img_draw.text((x, y), f"Level {server_level} - # {self._get_rank(member)}",
                      font=_font(sz))
        buf = io.BytesIO()
        img.save(fp=buf, format="png")
        buf.seek(0)
        await ctx.send(file=(discord.File(buf, "profile.png")))


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Profile(bot))
