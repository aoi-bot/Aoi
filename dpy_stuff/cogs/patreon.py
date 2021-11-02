import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

import aiohttp
from discord.ext import commands, tasks

from aoi import bot

if os.getenv("PATREON_ID") and os.getenv("PATREON_SECRET"):  # noqa c901
    logging.getLogger("aoi").info("Loading Patreon cog definition")

    class Patreon(commands.Cog):
        """
        THIS COG IS LOADED CONDITIONALLY

        - both PATREON_ID and PATREON_SECRET must exist to load this cog
        """

        def __init__(self, bot: bot.AoiBot):
            self.bot = bot
            self.patrons: Dict[int, int] = {}
            self.patreon_resp = {}
            self.lock = asyncio.Lock()
            self.refresh_patreon_pledges.start()

        @property
        def description(self) -> str:
            return "Patreon Cog"

        @tasks.loop(minutes=5)
        async def refresh_patreon_pledges(self):
            await self.bot.wait_until_ready()
            async with self.lock:
                async with aiohttp.request(
                    "GET",
                    f"https://api.patreon.com/oauth2/api/campaigns/{self.bot.patreon_id}/pledges",
                    headers={"Authorization": f"Bearer {self.bot.patreon_secret}"},
                ) as req:
                    json = await req.json()
                    self.patrons = {}
                    for user in json["data"]:
                        try:
                            self.patrons[user["relationships"]["patron"]["data"]["id"]] = user["attributes"][
                                "amount_cents"
                            ]
                        except KeyError:
                            pass
                self.patreon_resp = json

        @commands.cooldown(1, 30, commands.BucketType.user)
        @commands.command(brief="Claim patreon rewards", aliases=["clpar"])
        async def claimpatreon(self, ctx: bot.AoiContext):
            async with self.lock:
                user_id = str(ctx.author.id)
                patreon_user = ""
                for user in self.patreon_resp["included"]:
                    if user["type"] != "user":
                        continue
                    try:
                        patreon_discord_user_id = user["attributes"]["social_connections"]["discord"]["user_id"]
                    except KeyError:
                        continue
                    if user_id == patreon_discord_user_id:
                        patreon_user = user["id"]
                        break
                else:
                    return await ctx.send_error(
                        "It doesn't look like you're a [patron]"
                        "(https://www.patreon.com/crazygmr101). If you've recently pledged, "
                        "make sure you've [connected your discord]"
                        "(https://support.patreon.com/hc/en-us/articles/212052266-Get-my-Discord-role)"  # noqa
                        ", and waited at least 5 minutes."
                    )
                row = await (
                    await self.bot.db.conn.execute("select * from patreon where user=?", (int(user_id),))
                ).fetchone()  # noqa
                dt = datetime.now()
                dtf = f"{dt.month:0>2}{dt.year}"
                if not row:
                    await self.bot.db.conn.execute("insert into patreon values (?,?)", (int(user_id), dtf))
                    await self.bot.db.conn.commit()
                    cur = int(self.patrons[patreon_user])
                    await self.bot.db.award_global_currency(ctx.author, cur)
                    return await ctx.send_ok(f"Awarded you ${cur}. Thanks for supporting! ♥")
                if row[1] == dtf:
                    return await ctx.send_error("You've already claimed your reward this month.")
                cur = int(self.patrons[patreon_user])
                await self.bot.db.award_global_currency(ctx.author, cur)
                await self.bot.db.conn.execute("update patreon set last_claim=? where user=?", (dtf, int(user_id)))
                await self.bot.db.conn.commit()
                await ctx.send_ok(f"Awarded you ${cur}. Thanks for supporting! ♥")


else:

    class Patreon(commands.Cog):
        pass


def setup(bot: bot.AoiBot) -> None:
    if not bot.patreon_id or not bot.patreon_secret:
        bot.logger.warn("patreon:Not loading cog")
        bot.logger.warn("patreon: both PATREON_ID and PATREON_CAMPAIGN must be present in .env")
    bot.add_cog(Patreon(bot))
