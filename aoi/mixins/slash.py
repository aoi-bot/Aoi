import io
from typing import List, Tuple, Union

from PIL import Image
from discord_slash import SlashContext

import discord


class SlashMixin:
    async def embed(self, ctx: SlashContext,
                    author: str = None,
                    description: str = None,
                    title: str = None,
                    title_url: str = None,
                    fields: List[Tuple[str, str]] = None,
                    thumbnail: str = None,
                    clr: discord.Colour = discord.Embed.Empty,
                    image: Union[str, io.BufferedIOBase] = None,
                    footer: str = None,
                    not_inline: List[int] = [],
                    trash_reaction: bool = False):
        embed = discord.Embed(
            title=title,
            description=description,
            colour=clr,
            title_url=title_url
        )
        if author:
            embed.set_author(name=author)
        if image:
            if isinstance(image, str):
                embed.set_image(url=image)
                f = None
            elif isinstance(image, Image.Image):
                buf = io.BytesIO()
                image.save(buf, "png")
                buf.seek(0)
                f = discord.File(buf, filename="image.png")
                embed.set_image(url="attachment://image.png")
            else:
                image.seek(0)
                f = discord.File(image, filename="image.png")
                embed.set_image(url="attachment://image.png")
        else:
            f = None
        if footer:
            embed.set_footer(text=footer)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        for n, r in enumerate(fields or []):
            embed.add_field(name=r[0], value=r[1] or "None", inline=n not in not_inline)
        await ctx.channel.send(embed=embed, file=f)
