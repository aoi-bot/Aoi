from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.aoi import AoiBot


class Dashboard:
    def __init__(self, bot):
        self.bot: AoiBot = bot

    def run(self):
        self.bot.logger.info("dash:Starting")
