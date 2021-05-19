import os

from discord_slash import SlashCommand, cog_ext, SlashContext
from discord_slash.utils import manage_commands

import aoi
import discord
from discord.ext import commands
from libs.converters import AoiColor
from libs.expressions import evaluate

BASE = "https://discord.com/api/v8"

COMMANDS = {
    "color": [
        "Show a color",
        [
            {
                "type": 3,
                "name": "color",
                "description": "The color to show",
                "required": True
            }
        ]
    ],
    "slashes": [
        "View activated slash commands"
    ],
    "gradient": [
        "Show a list of colors",
        [
            {
                "type": 3,
                "name": "color1",
                "description": "First color",
                "required": True
            },
            {
                "type": 3,
                "name": "color2",
                "description": "Second color",
                "required": True
            },
            {
                "type": 4,
                "name": "num",
                "description": "Number of colors",
                "required": True
            },
            {
                "type": 5,
                "name": "hls",
                "description": "HLS gradient instead of RGB",
                "default": False
            }
        ]
    ]
}


class Slash(commands.Cog, aoi.SlashMixin, aoi.ColorCogMixin):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        del bot.slash
        bot.slash = SlashCommand(bot, sync_commands=True)
        self.bot.slash.get_cog_commands(self)
        # bot.loop.create_task(self.register_commands())
        super(Slash, self).__init__()

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @property
    def description(self) -> str:
        return "Slash commands"

    @cog_ext.cog_slash(name="slashes", description="Activated slash commands")
    async def _slashes(self, ctx: SlashContext):
        await ctx.send(hidden=True, content="Enabled slash commands on Aoi:\n"
                                            "`/color [color]`\n"
                                            "`/gradient [color1] [color2] [num] [hls]`\n"
                                            "`/calc [expression]`")

    @cog_ext.cog_slash(name="color")
    async def _color(self, ctx: SlashContext, color: str):
        try:
            clr: AoiColor = await AoiColor.convert(ctx, color)
        except commands.BadColourArgument:
            return await ctx.send(content=f"`{color}` is an invalid color. Aoi supports CSS color names "
                                          f"and colors in the formats `#rgb` and `#rrggbb`")
        await ctx.ack(False)
        await self.embed(ctx, title=str(clr), image=self._color_buf(clr))

    @cog_ext.cog_slash(name="gradient")
    async def _gradient(self, ctx: SlashContext, color1: str, color2: str, num: int, hls: bool = False):
        try:
            color1: AoiColor = await AoiColor.convert(ctx, color1)
        except commands.BadColourArgument:
            return await ctx.send(content=f"`{color1}` is an invalid color. Aoi supports CSS color names "
                                          f"and colors in the formats `#rgb` and `#rrggbb`")
        try:
            color2: AoiColor = await AoiColor.convert(ctx, color2)
        except commands.BadColourArgument:
            return await ctx.send(content=f"`{color2}` is an invalid color. Aoi supports CSS color names "
                                          f"and colors in the formats `#rgb` and `#rrggbb`")
        try:
            buf, colors = self._gradient_buf(color1, color2, num, hls)
        except commands.BadArgument as e:
            return await ctx.send(content=str(e))
        await ctx.ack(False)
        await self.embed(ctx, title="Gradient",
                         description=" ".join("#" + "".join(hex(x)[2:].rjust(2, "0") for x in c) for c in colors),
                         image=buf)

    @cog_ext.cog_slash(name="calc", description="Calculate an expression", options=[
        {
            "type": 3,
            "name": "expr",
            "description": "The expression",
            "required": True
        }
    ])
    async def _calc(self, ctx: SlashContext, expr: str):
        try:
            res = await evaluate(expr)
        except aoi.CalculationSyntaxError:
            await ctx.send(hidden=True, content="Syntax error")
        except aoi.DomainError as e:
            await ctx.send(hidden=True, content=f"Domain error for {e}")
        except aoi.MathError:
            await ctx.send(hidden=True, content="Math error")
        else:
            await ctx.send(hidden=True, content=f"Expression: {discord.utils.escape_markdown(expr)}\n"
                                                f"Result:\n{res}")

    async def register_commands(self):
        await self.bot.wait_until_ready()
        # await manage_commands.remove_all_commands(self.bot.user.id, os.getenv("TOKEN"), None)
        cmds = await manage_commands.get_all_commands(self.bot.user.id, os.getenv("TOKEN"), None)
        print(cmds)


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Slash(bot))
