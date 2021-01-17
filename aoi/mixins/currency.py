import asyncio
import random
from typing import Dict, Tuple, List, Optional

import discord
from libs.conversions import escape
from ..aoi_bot import AoiBot
from ..custom_context import AoiContext


class CurrencyMixin:
    def __init__(self, bot: AoiBot):
        self.bot = bot
        self.active_catches: Dict[discord.TextChannel, List[Tuple[discord.Message, int]]] = {}
        self.lock = asyncio.Lock()

    async def maybe_gen_currency(self, msg: discord.Message):
        gs = await self.bot.db.guild_setting(msg.guild.id)
        prefix = escape((await self.bot.get_prefix(msg))[-1], msg)
        if gs.currency_chance == 0:
            return
        if not gs.currency_gen_channels:
            return
        if msg.channel.id not in gs.currency_gen_channels:
            return
        if random.randint(0, 100) >= gs.currency_chance:
            return

        amount = random.randint(gs.currency_min, gs.currency_max + 1)

        with open("assets/currency_mokke.png", "rb") as fp:
            file = discord.File(fp, filename="mokke.png")

        if gs.reply_embeds:
            msg: discord.Message = await msg.channel.send(embed=discord.Embed(description=random.choice([
                f"A mokke passes by you carrying ${amount}. `{prefix}grab` it.",
                f"You see a mokke with ${amount}! `{prefix}grab` it!"
            ]
            )).set_image(url="attachment://mokke.png"), file=file)
        else:
            msg: discord.Message = await msg.channel.send(
                random.choice(["<:mokke:798002325036728350>",
                               "<:mokke_jump:798073920104169492>"]) +
                random.choice([
                    f" A mokke passes by you carrying ${amount}. `{prefix}grab` it.",
                    f" You see a mokke with ${amount}! `{prefix}grab` it!"
                ])
            )

        async with self.lock:
            if msg.channel not in self.active_catches:
                self.active_catches[msg.channel] = [(msg, amount)]
            else:
                self.active_catches[msg.channel].append((msg, amount))

    async def _grab(self, ctx: AoiContext) -> Optional[int]:
        async with self.lock:
            if ctx.channel not in self.active_catches:
                return None
            if not self.active_catches[ctx.channel]:
                return None

            messages: List[discord.Message] = [catch[0] for catch in self.active_catches[ctx.channel]]
            amount: int = sum(catch[1] for catch in self.active_catches[ctx.channel])
            del self.active_catches[ctx.channel]

        asyncio.create_task(self.bot.http.delete_messages(ctx.channel.id, [m.id for m in messages]))
        await self.bot.db.award_guild_currency(ctx.author, amount)
        return amount
