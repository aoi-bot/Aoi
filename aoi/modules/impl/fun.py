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
from textwrap import dedent

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps
import aiohttp
import hikari
import tanjun

from aoi.bot import injected
from aoi.libs.minesweeper import MinesweeperError, SpoilerMinesweeper


def _font(size: int) -> PIL.ImageFont.ImageFont:
    return PIL.ImageFont.truetype("assets/merged.ttf", size=size)


simp_fp = open("assets/simp-template.png", "rb")
simp_img = PIL.Image.open(simp_fp)
av_mask = PIL.Image.new("L", simp_img.size, 0)
av_mask_draw = PIL.ImageDraw.Draw(av_mask)
av_mask_draw.ellipse((430, 384, 430 + 83, 384 + 83), fill=255)


async def anime_quote(
    ctx: typing.Union[tanjun.abc.SlashContext, tanjun.abc.MessageContext],
    _embed: injected.EmbedCreator,
):
    async with aiohttp.ClientSession() as sess:
        async with sess.get("https://animechan.vercel.app/api/random") as resp:
            if resp.status == 200:
                master_resp = await resp.json()
                await ctx.respond(
                    f"> {master_resp['quote']}" f"~ {master_resp['character']}" f"Anime: {master_resp['anime']}"
                )
            else:
                await ctx.respond(f"API returned code: `{resp.status}`. Try again later...")


async def minesweeper(
    ctx: typing.Union[tanjun.abc.SlashContext, tanjun.abc.MessageContext],
    height: int,
    width: int,
    bombs: int,
    raw: bool,
    no_spoiler: bool,
    _embed: injected.EmbedCreator,
):
    try:
        await ctx.respond(
            ("```%s```" if raw else "%s") % SpoilerMinesweeper(height, width, bombs).discord_str(no_spoiler)
        )
    except MinesweeperError as e:
        await ctx.respond(embed=_embed.error_embed(ctx, description=str(e)))


async def waifu(ctx: typing.Union[tanjun.abc.SlashContext, tanjun.abc.MessageContext]):
    async with aiohttp.ClientSession() as sess:
        async with sess.get("https://api.waifu.pics/sfw/waifu") as resp:
            await ctx.respond(embed=hikari.Embed(title="A waifu").set_image((await resp.json())["url"]))


async def simp(
    ctx: typing.Union[tanjun.abc.SlashContext, tanjun.abc.MessageContext],
    _member: typing.Optional[hikari.Member],
):
    member: hikari.Member = _member or ctx.cache.get_guild(ctx.guild_id).get_member(ctx.author.id)
    bounds = (490, 145, 685, 178)
    target_width = bounds[2] - bounds[0]
    img_copy: PIL.Image = simp_img.copy().convert("RGBA")

    draw = PIL.ImageDraw.Draw(img_copy)
    # draw.rectangle(bounds, fill=(0, 200, 0))
    font = _font(33)
    name_size, name_height = draw.textsize(member.username, font=font)
    sz = 33
    while name_size > target_width and sz > 4:
        sz -= 1
        font = _font(sz)
        name_size, name_height = draw.textsize(member.username, font=font)
    draw.text(
        (587 - name_size / 2, 162 - name_height / 2),
        text=member.username,
        font=font,
        fill=(0, 0, 0),
    )

    av_buf = io.BytesIO()
    async with member.make_avatar_url(ext="png", size=128).stream() as stream:
        av_buf.write(await stream.read())
    av_buf.seek(0)
    av_img = PIL.Image.open(av_buf).convert("RGBA")
    av_img = av_img.resize((83, 83))

    av_fg_img = PIL.Image.new("RGBA", simp_img.size)
    av_fg_img.paste(av_img, (430, 384))
    av_fg_img.putalpha(av_mask)

    img_copy = PIL.Image.alpha_composite(img_copy, av_fg_img)

    buf = io.BytesIO()
    img_copy.save(buf, "png")
    buf.seek(0)
    await ctx.respond(attachment=buf)
