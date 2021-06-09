from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aoi import AoiBot


class Dashboard:
    def __init__(self, bot):
        self.bot: AoiBot = bot

    def run(self):
        c = 0
        self.bot.logger.info("dash:Starting")