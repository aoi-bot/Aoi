import io
from typing import Optional

import PIL
import PIL.ImageDraw as Dw
import PIL.ImageFont as Fn

import aoi
import discord
from aoi.mixins.currency import CurrencyMixin
from discord.ext import commands
from libs.converters import disenable


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


def _center(x, y, x2, y2, w, h):
    return (x + x2) / 2 - w / 2, (y + y2) / 2 - h / 2


def _fit(w, h, text, size, draw, *, w_pad=5, h_pad=5):
    _w, _h = draw.textsize(text, font=_font(size))
    while ((_w > w - w_pad * 2) or (_h > h - h_pad * 2)) and size > 4:
        size -= 1
        _w, _h = draw.textsize(text, font=_font(size))
    return _w, _h, size


def _center_and_fit(x, y, x2, y2, text, size, draw, *, w_pad=5, h_pad=5):
    w, h, sz = _fit(abs(x - x2), abs(y - y2), text, size, draw, w_pad=w_pad, h_pad=h_pad)
    x, y = _center(x, y, x2, y2, w, h)
    return x, y, w, h, sz


def _font(size: int) -> PIL.ImageFont.ImageFont:
    return Fn.truetype(
        "assets/merged.ttf", size=size)


class Currency(commands.Cog, CurrencyMixin):
    def __init__(self, bot: aoi.AoiBot):
        CurrencyMixin.__init__(self, bot)
        self.bot = bot
        self.fp = open("assets/wallet.png", "rb")
        self.background: PIL.Image.Image = PIL.Image.open(self.fp)
        self.level_font: PIL.ImageFont.ImageFont = _font(42)

    @property
    def description(self):
        return "Commands dealing with currency"

    @commands.is_owner()
    @commands.command(
        brief="Give or take currency globally"
    )
    async def award_g(self, ctx: aoi.AoiContext, member: Optional[discord.Member], amount: int):
        member = member or ctx.author
        await self.bot.db.award_global_currency(member, amount)
        await ctx.send_info(f"Added ${amount} to {member.mention}. Their new total is "
                            f"{await self.bot.db.get_global_currency(member)}.")

    @commands.command(
        brief="Checks your wallet",
        aliases=["$"]
    )
    async def wallet(self, ctx: aoi.AoiContext, member: discord.Member = None):
        member = member or ctx.author
        img = self.background.copy()
        draw = Dw.Draw(img)
        await self.bot.db.ensure_global_currency_entry(member)
        if not (await self.bot.db.guild_setting(ctx.guild.id)).reply_embeds:
            return await ctx.send(f"**{member}'s Wallet**\n*"
                                  f"*Global**: ${await self.bot.db.get_global_currency(member):,}\n"
                                  f"**Server**: ${await self.bot.db.get_guild_currency(member):,}")
        for i in range(3):
            x, y, _, _, sz = _center_and_fit(
                [14, 78, 78][i],
                [66, 146, 226][i] - 52,
                498,
                [66, 146, 226][i],
                [
                    member.name,
                    f"${await self.bot.db.get_global_currency(member):,}",
                    f"${await self.bot.db.get_guild_currency(member):,}"
                ][i],
                40,
                draw
            )
            draw.text((x, y), [
                member.name,
                f"${await self.bot.db.get_global_currency(member):,}",
                f"${await self.bot.db.get_guild_currency(member):,}"
            ][i], fill=(0, 0, 0), font=_font(sz))
        buf = io.BytesIO()
        img.save(fp=buf, format="png")
        buf.seek(0)
        await ctx.send(file=(discord.File(buf, "profile.png")))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        for i in await self.bot.get_prefix(message):
            if message.content.startswith(i):
                return
        await self.maybe_gen_currency(message)

    @commands.command(brief="Catch currency")
    async def grab(self, ctx: aoi.AoiContext):
        amount = await self._grab(ctx)
        if amount is not None:
            await ctx.send_ok(f"Grabbed ${amount}")

    @commands.has_permissions(manage_guild=True)
    @commands.command(brief="Turn currency generation for a channel on or off")
    async def gencur(self, ctx: aoi.AoiContext, channel: Optional[discord.TextChannel], state: disenable()):
        channel = channel or ctx.channel
        if state.lower() == "enable":
            if channel.id not in (await self.bot.db.guild_setting(ctx.guild.id)).currency_gen_channels:
                await self.bot.db.add_currency_channel(channel)
                return await ctx.send_ok(f"Currency will now generate in {channel.mention}")
            return await ctx.send_ok(f"Currency can already generate in {channel.mention}")
        if channel.id in (await self.bot.db.guild_setting(ctx.guild.id)).currency_gen_channels:
            await self.bot.db.remove_currency_channel(channel)
            return await ctx.send_ok(f"Currency will not generate in {channel.mention}")
        return await ctx.send_ok(f"Currency already couldn't generate in {channel.mention}")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Currency(bot))
