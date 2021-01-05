import random
from typing import List

import aoi
from discord.ext import commands
from wrappers import gelbooru


class NSFW(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.gelbooru = None
        bot.loop.create_task(self._init())

    @property
    def description(self):
        return ":smirk:"

    async def _init(self):
        self.bot.logger.info("gelb:Waiting for bot")
        await self.bot.wait_until_ready()
        self.gelbooru = gelbooru.GelbooruBrowser(
            api_key=self.bot.gelbooru_key,
            user_id=self.bot.gelbooru_user,
            banned_tags=self.bot.banned_tags
        )
        self.bot.logger.info("gelb:Ready!")

    @commands.is_nsfw()
    @commands.command(brief="Find a random gelbooru post by tag")
    async def gelbooru(self, ctx: aoi.AoiContext, *, tags: str):
        posts: List[gelbooru.GelbooruPost]
        posts, f_tag, f_post = await self.gelbooru.get_posts(tags.split())
        if not posts:
            return await ctx.send_error("No results were found for that search.")
        post = random.choice(posts)
        await ctx.embed(
            image=post.image_url,
            description=f"[Page]({post.page})",
            footer="Some images/tags were filtered from the search query and/or "
                   "results to comply with discord Terms of Service"
            if f_tag or f_post else "",
            trash_reaction=False
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(NSFW(bot))
