import io
import itertools
import sys
import traceback
from typing import Dict, Union

import aiohttp
import discord
import PIL
import PIL.Image as Im
import PIL.ImageDraw as Dw
import PIL.ImageFont as Fn
from discord.ext import commands

import bot

lvl_list = [0] + [8 * lvl + 40 for lvl in range(100000)]
ttl_lvl_list = list(itertools.accumulate(lvl_list))


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(
        (
            (img_width - crop_width) // 2,
            (img_height - crop_height) // 2,
            (img_width + crop_width) // 2,
            (img_height + crop_height) // 2,
        )
    )


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def _cur_string(cur: int):
    neg = abs(cur) != cur
    cur = abs(cur)
    if cur < 1000:
        return f"{'-' if neg else ''}${cur}"
    elif cur < 100000:
        return f"{'-' if neg else ''}${round(cur / 100) / 10}K"
    elif cur < 1000000:
        return f"{'-' if neg else ''}${round(cur / 1000)}K"
    elif cur < 1000000000:
        return f"{'-' if neg else ''}${round(cur / 1000000)}M"
    elif cur < 1000000000000:
        return f"{'-' if neg else ''}${round(cur / 1000000000)}B"


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
        size -= 1
        _w, _h = draw.textsize(text, font=_font(size))
    return _w, _h, size


def _center_and_fit(x, y, x2, y2, text, size, draw, *, w_pad=5, h_pad=5):
    w, h, sz = _fit(
        abs(x - x2), abs(y - y2), text, size, draw, w_pad=w_pad, h_pad=h_pad
    )
    x, y = _center(x, y, x2, y2, w, h)
    return x, y, w, h, sz


def _font(size: int) -> PIL.ImageFont.ImageFont:
    return Fn.truetype("assets/merged.ttf", size=size)


def _16(*args: Union[float, int]) -> [Union[float, int], ...]:
    return tuple(map(lambda x: 16 * x, args))


# noinspection PyUnresolvedReferences
class Profile(commands.Cog):
    def __init__(self, bot: bot.AoiBot):
        self.bot = bot
        self.fp = open("assets/profile.png", "rb")
        self.background: PIL.Image.Image = PIL.Image.open(self.fp)
        self.level_font: PIL.ImageFont.ImageFont = _font(42)
        self._buf = io.BytesIO()
        self.default_bg = None
        bot.loop.create_task(self._init())

    async def _init(self):
        async with aiohttp.ClientSession() as sess:
            async with sess.get("https://i.imgur.com/3b42LpU.jpg") as resp:
                self._buf.write(await resp.content.read())
        self._buf.seek(0)
        self.default_bg = Im.open(self._buf)

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

    @commands.command(brief="View someone's profile")
    async def profile(self, ctx: bot.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        try:
            _, _, _, _, bg = await self.bot.db.get_badges_titles(member)
            if not bg:
                card_bg = self.default_bg.copy()
            else:
                _buf = io.BytesIO()
                async with aiohttp.ClientSession() as sess:
                    async with sess.get(bg) as resp:
                        resp.raise_for_status()
                        _buf.write(await resp.content.read())
                _buf.seek(0)
                card_bg = Im.open(_buf)
                card_bg = crop_max_square(card_bg)
                card_bg = card_bg.resize((512, 512))
        except Exception as error:  # noqa
            card_bg = self.default_bg.copy()
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )
        card_bg = card_bg.convert("RGBA")
        await self.bot.db.ensure_xp_entry(member)
        global_xp = self.bot.db.global_xp[member.id]
        server_xp = self.bot.db.xp[ctx.guild.id][member.id]
        global_level, global_rem = _level(global_xp)
        server_level, server_rem = _level(server_xp)
        avatar_buf = io.BytesIO()
        await member.avatar.save(avatar_buf)
        avatar_buf.seek(0)
        img = self.background.copy()
        avatar_img = Im.open(avatar_buf)
        avatar_img = avatar_img.resize((128, 128))
        img_draw = Dw.Draw(img)
        img.paste(avatar_img, (32, 32))
        avatar_buf.close()

        # create overlays for the xp bars
        global_width = 330.66672 * global_rem / _xp_per_level(global_level + 1)
        global_xp_poly = (
            (133.33328, 192),
            (133.33328 + global_width, 192),
            (117.33328 + global_width, 240),
            (117.33328, 240),
        )

        server_width = 330.66672 * server_rem / _xp_per_level(server_level + 1)
        server_xp_poly = (
            (112, 256),
            (112 + server_width, 256),
            (96 + server_width, 304),
            (96, 304),
        )
        overlay = Im.new("RGBA", img.size, (0, 0, 0, 0))
        Dw.Draw(overlay).polygon(global_xp_poly, fill=(0, 0, 0) + (120,))
        Dw.Draw(overlay).polygon(server_xp_poly, fill=(0, 0, 0) + (120,))
        img = PIL.Image.alpha_composite(img, overlay)
        img_draw = Dw.Draw(img)

        # draw text
        await self.bot.db.ensure_user_entry(member)
        x, y, _, _, sz = _center_and_fit(
            454,
            162,
            190,
            111,
            (await self.bot.db.get_titles(member))[0],
            32,
            img_draw,
            w_pad=24,
        )
        img_draw.text((x, y), (await self.bot.db.get_titles(member))[0], font=_font(sz))

        x, y, _, _, sz = _center_and_fit(
            217.6, 80, 480, 32, member.name, 32, img_draw, w_pad=24
        )
        img_draw.text((x, y), member.name, font=_font(sz))

        x, y, _, _, sz = _center_and_fit(
            115.8,
            191,
            480,
            242,
            f"Level {global_level} - # {self._get_global_rank(member)}",
            32,
            img_draw,
            w_pad=24,
        )
        img_draw.text(
            (x, y),
            f"Level {global_level} - # {self._get_global_rank(member)}",
            font=_font(sz),
        )

        x, y, _, _, sz = _center_and_fit(
            95,
            255,
            459.2,
            306,
            f"Level {server_level} - # {self._get_rank(member)}",
            32,
            img_draw,
            w_pad=24,
        )
        img_draw.text(
            (x, y), f"Level {server_level} - # {self._get_rank(member)}", font=_font(sz)
        )

        x, y, _, _, sz = _center_and_fit(
            115.8,
            319,
            257.5,
            370,
            f"{_cur_string(await self.bot.db.get_global_currency(member))}",
            32,
            img_draw,
            w_pad=24,
        )
        img_draw.text(
            (x, y),
            f"{_cur_string(await self.bot.db.get_global_currency(member))}",
            font=_font(sz),
        )

        x, y, _, _, sz = _center_and_fit(
            94.5,
            383,
            236.2,
            434,
            f"{_cur_string(await self.bot.db.get_guild_currency(member))}",
            32,
            img_draw,
            w_pad=24,
        )
        img_draw.text(
            (x, y),
            f"{_cur_string(await self.bot.db.get_guild_currency(member))}",
            font=_font(sz),
        )
        card_bg = card_bg.convert("RGBA")
        img = Im.alpha_composite(card_bg, img)
        buf = io.BytesIO()
        img.save(fp=buf, format="png")
        buf.seek(0)
        await ctx.send(file=(discord.File(buf, "profile.png")))

    @commands.command(brief="Change your profile card for $7500 (global)")
    async def profilecard(self, ctx: bot.AoiContext, url: str):
        if await self.bot.db.get_global_currency(ctx.author) < 7500:
            return await ctx.send_error(
                "You don't have enough global currency for this."
            )
        try:
            cur_removed = False
            # make sure that the user has a record in the db
            _, _, _, _, _ = await self.bot.db.get_badges_titles(ctx.author)
            _buf = io.BytesIO()
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url) as resp:
                    resp.raise_for_status()
                    _buf.write(await resp.content.read())
            _buf.seek(0)
            card_bg = Im.open(_buf)
            card_bg = crop_max_square(card_bg)
            card_bg = card_bg.resize((512, 512))
            _buf2 = io.BytesIO()
            card_bg.save(_buf2, format="png")
            await ctx.embed(image=_buf2, trash_reaction=False)
            if await ctx.confirm(
                "Set this image as your background?", "Image set", "Image not set"
            ):
                await self.bot.db.award_global_currency(ctx.author, -7500)
                cur_removed = True
                if ctx.author.id not in self.bot.db.changed_global_users:
                    self.bot.db.changed_global_users.append(ctx.author.id)
                self.bot.db.backgrounds[ctx.author.id] = url
                await self.bot.db.cache_flush()
        except Exception as error:  # noqa
            if cur_removed:  # noqa
                await self.bot.db.award_global_currency(ctx.author, 7500)
            await ctx.send_error(
                "An error occured while setting the background - your currency was not "
                "affected"
            )
            traceback.print_exception(
                type(error), error, error.__traceback__, file=sys.stderr
            )


def setup(bot: bot.AoiBot) -> None:
    bot.add_cog(Profile(bot))
