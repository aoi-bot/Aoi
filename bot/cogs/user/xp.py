import io
import itertools
from typing import Dict, Tuple

import PIL
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from bot import aoi
import discord
from discord.ext import commands

# xp levelling functions
lvl_list = [0] + [8 * lvl + 40 for lvl in range(100000)]
ttl_lvl_list = list(itertools.accumulate(lvl_list))


def _xp_per_level(lvl: int):
    return lvl_list[lvl]


def _level(xp: int):
    for n, v in enumerate(ttl_lvl_list):
        if v > xp:
            return n - 1, lvl_list[n] - (v - xp)


def _font(size: int) -> PIL.ImageFont.ImageFont:
    return PIL.ImageFont.truetype(
        "assets/merged.ttf", size=size)


# noinspection PyUnresolvedReferences
class XP(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.fp = open("assets/background.png", "rb")
        self.xp_img: PIL.Image.Image = PIL.Image.open(self.fp)
        self.fp_g = open("assets/g_background.png", "rb")
        self.g_xp_img: PIL.Image.Image = PIL.Image.open(self.fp_g)
        self.level_font: PIL.ImageFont.ImageFont = _font(42)
        self.text_font: PIL.ImageFont.ImageFont = _font(30)

    @property
    def description(self):
        return "Commands dealing with XP"

    @commands.is_owner()
    @commands.command(
        brief="Reloads the xp images"
    )
    async def xpr(self, ctx: aoi.AoiContext):
        self.fp.close()
        self.fp_g.close()
        self.fp = open("assets/background.png", "rb")
        self.xp_img: PIL.Image.Image = PIL.Image.open(self.fp)
        self.fp_g = open("assets/g_background.png", "rb")
        self.g_xp_img: PIL.Image.Image = PIL.Image.open(self.fp_g)
        self.level_font: PIL.ImageFont.ImageFont = _font(42)
        self.text_font: PIL.ImageFont.ImageFont = _font(30)
        await ctx.send_ok("Images and fonts reloaded")

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

    async def _xp_template(self, ctx: aoi.AoiContext, member: discord.Member,
                           rank_func: callable, color: Tuple[int, int, int],
                           template, xp):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        l, x = _level(xp)
        r = rank_func(member)
        img = template.copy()
        poly_width = 243 * x / _xp_per_level(l + 1)
        poly = [(119, 11), (112, 59), (112 + poly_width, 59), (119 + poly_width, 11)]
        overlay = PIL.Image.new("RGBA", img.size, (0, 0, 0, 0))
        PIL.ImageDraw.Draw(overlay).polygon(poly, fill=color + (80,))
        img = PIL.Image.alpha_composite(img, overlay)
        draw = PIL.ImageDraw.Draw(img)
        draw.text((8, 75), text=f"#{r}", font=_font(24),
                  fill=color)
        draw.text((21, 13), text=str(l), font=self.level_font,
                  fill=color)
        name_font = _font(30)
        name_size, name_height = draw.textsize(member.name, font=self.text_font)
        sz = 30
        while name_size > 330 and sz > 4:
            sz -= 1
            print(f"try {sz}")
            name_font = _font(sz)
            name_size, name_height = draw.textsize(member.name, font=name_font)
        # y 15 x 190 64
        draw.text((190 - name_size / 2, 214 - name_height / 2), text=member.name, font=name_font,
                  fill=color)
        rem_level_size = draw.textsize(f"{x}/"
                                       f"{_xp_per_level(l + 1)}", font=self.text_font)[0]
        # y 10 x 111 364
        draw.text((230 - rem_level_size / 2, 19), text=f"{x}/"
                                                       f"{_xp_per_level(l + 1)}", font=self.text_font,
                  fill=color)
        return img

    async def _xp_values(self, ctx: aoi.AoiContext, member: discord.Member,
                         rank_func: callable, xp: int):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        level, partial = _level(xp)
        rank = rank_func(member)
        required = _xp_per_level(level + 1)
        return level, partial, rank, required

    @commands.command(
        brief="Gets the XP of a user"
    )
    async def xp(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        if not await ctx.using_embeds():
            level, partial, rank, required = \
                await self._xp_values(ctx, member, self._get_rank, self.bot.db.xp[ctx.guild.id][member.id])
            return await ctx.send(f"**{member}'s Server XP**\n"
                                  f"#**{rank}**  Level: **{level}**  **{partial}**/**{required}**")
        buf = io.BytesIO()
        (await self._xp_template(ctx, member, self._get_rank, (130, 36, 252), self.xp_img,
                                 self.bot.db.xp[ctx.guild.id][member.id])).save(fp=buf, format="PNG")
        buf.seek(0)
        await ctx.send(file=(discord.File(buf, "xp.png")))

    @commands.command(
        brief="Gets the global XP of a user"
    )
    async def gxp(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        if not await ctx.using_embeds():
            level, partial, rank, required = \
                await self._xp_values(ctx, member, self._get_global_rank,
                                      self.bot.db.global_xp[member.id])
            return await ctx.send(f"**{member}'s Global XP**\n"
                                  f"#**{rank}**  Level: **{level}**  **{partial}**/**{required}**")
        buf = io.BytesIO()
        (await self._xp_template(ctx, member,
                                 self._get_global_rank, (0xff, 0x2a, 0x5b),
                                 self.g_xp_img, self.bot.db.global_xp[member.id])).save(fp=buf, format="PNG")
        buf.seek(0)
        await ctx.send(file=(discord.File(buf, "gxp.png")))

    @commands.is_owner()
    @commands.command(
        brief="Set a user's xp"
    )
    async def setxp(self, ctx: aoi.AoiContext, xp: int, member: discord.Member = None):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        self.bot.db.xp[member.guild.id][member.id] = xp
        await self.bot.db.cache_flush()
        await ctx.send_ok(f"{member.mention}'s xp set to {xp}")

    @commands.is_owner()
    @commands.command(
        brief="Add to a user's xp"
    )
    async def addxp(self, ctx: aoi.AoiContext, xp: int, member: discord.Member = None):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        self.bot.db.xp[member.guild.id][member.id] += xp
        if self.bot.db.xp[member.guild.id][member.id] < 0:
            self.bot.db.xp[member.guild.id][member.id] = 0
        await self.bot.db.cache_flush()
        await ctx.send_ok(f"{abs(xp)} xp {'added to' if xp >= 0 else 'taken from'} {member.mention}")

    @commands.command(
        brief="Checks server xp leaderboard"
    )
    async def xplb(self, ctx: aoi.AoiContext, page: int = 1):
        r = self._get_ranked(ctx.guild.id)
        _n_per_page = 10
        top_10 = {k: (n, r[k]) for n, k in enumerate(list(r.keys())[(page - 1) * _n_per_page:page * _n_per_page])}
        await ctx.embed(
            title="Leaderboard",
            fields=[
                (f"#{v[0] + 1 + (page - 1) * _n_per_page} {self.bot.get_user(k)}",
                 f"Level {_level(v[1])[0]} - {v[1]} xp") for k, v in top_10.items()
            ],
            not_inline=list(range(_n_per_page))
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(XP(bot))
