import aoi
from discord.ext import commands


class Searches(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Various search commands"

    @commands.command(
        brief="Search a tag on Imgur",
        aliases=["img"]
    )
    async def imgur(self, ctx: aoi.AoiContext, tag: str):
        try:
            img_id, album_id, album_link, description = await self.bot.imgur.random_by_tag(tag)
            await ctx.embed(
                title=description,
                description=f"[Link to post]({album_link})",
                title_url=album_link,
                image=f"https://i.imgur.com/{img_id}.jpg",
                footer=f"Imgur result for \"{tag}\" searched by {ctx.author}",
                trash_reaction=False
            )
        except KeyError:
            await ctx.send_error("No results found with that tag")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Searches(bot))
