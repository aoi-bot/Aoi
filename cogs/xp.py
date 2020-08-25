import io
import itertools

import PIL
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import discord
from discord.ext import commands

import aoi

# xp levelling functions
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


class XP(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        fp = open("assets/background.png", "rb")
        self.img: PIL.Image.Image = PIL.Image.open(fp)
        self.level_font: PIL.ImageFont.ImageFont = PIL.ImageFont.truetype(
            "assets/DejaVuSans-Oblique.ttf", size=42)
        self.text_font: PIL.ImageFont.ImageFont = PIL.ImageFont.truetype(
            "assets/DejaVuSans-Oblique.ttf", size=30)

    @commands.command()
    async def xp(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        xp = self.bot.db.xp[ctx.guild.id][member.id]
        l, x = _level(xp)
        buf = io.BytesIO()
        img = self.img.copy()
        draw = PIL.ImageDraw.Draw(img)
        draw.text((21, 13), text=str(l), font=self.level_font,
                  fill=(78, 1, 172))
        name_size = draw.textsize(member.name, font=self.text_font)[0]
        # y 15 x 190 64
        draw.text((190 - name_size / 2, 196), text=member.name, font=self.text_font,
                  fill=(78, 1, 172))
        rem_level_size = draw.textsize(f"{x}/"
                                       f"{_xp_per_level(l + 1)}", font=self.text_font)[0]
        # y 10 x 111 364
        draw.text((230 - rem_level_size / 2, 19), text=f"{x}/"
                                                       f"{_xp_per_level(l + 1)}", font=self.text_font,
                  fill=(78, 1, 172))
        img.save(fp=buf, format="png")
        buf.seek(0)
        await ctx.send(file=(discord.File(buf, "xp.png")))

    @commands.is_owner()
    @commands.command(
        brief="Flush XP to database manually"
    )
    async def flushxp(self, ctx: aoi.AoiContext):
        await self.bot.db.cache_flush()

    @commands.is_owner()
    @commands.command(
        brief="Set a user's xp"
    )
    async def setxp(self, ctx: aoi.AoiContext, xp: int, member: discord.Member = None):
        member = member or ctx.author
        await self.bot.db.ensure_xp_entry(member)
        self.bot.db.xp[member.guild.id][member.id] = xp
        await self.bot.db.cache_flush()


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(XP(bot))
