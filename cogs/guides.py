from discord.ext import commands

import aoi


class Guides(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self):
        return "Guides on how to use Aoi"

    @commands.command(brief="Shows the permission guide")
    async def permguide(self, ctx: aoi.AoiContext):
        await ctx.embed(
            title="Aoi Permission guide",
            description=
            f"Aoi's permissions are based off of a permission chain that "
            f"anyone can view with `{ctx.prefix}lp`. The chain is evaluated "
            f"from 0 to the top. The permission chain can be modified by anyone with "
            f"administrator permission in a server. `{ctx.prefix}cmds permissions` can "
            f"be used to view view a list of the permission commands\n"
            f"The chain can be reset to the default with {ctx.prefix}rp"
        )

    @commands.command(
        brief="Shows the currency guide"
    )
    async def currencyguide(self, ctx: aoi.AoiContext):
        await ctx.embed(
            title="Aoi Currency guide",
            description=f"There are two types of currency in Aoi: Server and Global.\n"
                        f"Global currency is gained at the rate of $3/message, and can only be gained "
                        f"once every 3 minutes. Global currency is used over in `{ctx.prefix}cmds globalshop` to "
                        f"buy a title for your card an over in `{ctx.prefix}profilecard` to buy a background change "
                        f"for your profile card.\n"
                        f"Server currency is gained at a rate set by the server staff, and is viewable with "
                        f"`{ctx.prefix}configs`. It is used for roles and gambling - see `{ctx.prefix}cmds ServerShop` "
                        f"and `{ctx.prefix}cmds ServerGambling`."
        )


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Guides(bot))
