from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import bot

from bot.errors import CurrencyError


class CurrencyLock:
    def __init__(
        self,
        ctx: bot.AoiContext,
        amount: int,
        is_global: bool,
        success: str,
        error: Optional[str] = "An error occurred, and your currency was not affected.",
    ):
        self.ctx = ctx
        self.amount = amount
        self.is_global = is_global
        self.bot: bot.AoiBot = ctx.bot
        self.success = success
        self.error = error

    async def __aenter__(self):
        if self.is_global:
            await self.bot.db.ensure_global_currency_entry(self.ctx.author)
            if await self.bot.db.get_global_currency(self.ctx.author) < self.amount:
                raise CurrencyError(
                    amount_has=await self.bot.db.get_global_currency(self.ctx.author),
                    amount_needed=self.amount,
                    is_global=True,
                )
        else:
            await self.bot.db.ensure_guild_currency_entry(self.ctx.author)
            if await self.bot.db.get_guild_currency(self.ctx.author) < self.amount:
                raise CurrencyError(
                    amount_has=await self.bot.db.get_guild_currency(self.ctx.author),
                    amount_needed=self.amount,
                    is_global=False,
                )
        if self.is_global:
            await self.bot.db.award_global_currency(self.ctx.author, -self.amount)
        else:
            await self.bot.db.award_guild_currency(self.ctx.author, -self.amount)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if self.error:
                await self.ctx.send_error(self.error)
                return False
            if self.is_global:
                await self.bot.db.award_global_currency(self.ctx.author, self.amount)
            else:
                await self.bot.db.award_guild_currency(self.ctx.author, self.amount)
            return True
        else:
            await self.ctx.send_ok(self.success)
