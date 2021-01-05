import io
import os
from typing import List, Tuple, Union

from PIL import Image, ImageDraw
from discord_slash import SlashCommand, cog_ext, SlashContext
from discord_slash.utils import manage_commands

import aoi
import discord
from discord.ext import commands
from libs.colors import rgb_gradient, hls_gradient
from libs.converters import AoiColor

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
        bot.slash = SlashCommand(bot, override_type=True)
        self.bot.slash.get_cog_commands(self)
        bot.loop.create_task(self.register_commands())
        super(Slash, self).__init__()

    def cog_unload(self):
        self.bot.slash.remove_cog_commands(self)

    @property
    def description(self) -> str:
        return "Slash commands"

    @cog_ext.cog_slash(name="color")
    async def _color(self, ctx: SlashContext, color: str):
        try:
            clr: AoiColor = await AoiColor.convert(ctx, color)
        except commands.BadColourArgument:
            return await ctx.send(content=f"`{color}` is an invalid color. Aoi supports CSS color names "
                                          f"and colors in the formats `#rgb` and `#rrggbb`")
        await ctx.send(send_type=5)
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
        await ctx.send(send_type=5)
        await self.embed(ctx, title="Gradient",
                         description=" ".join("#" + "".join(hex(x)[2:].rjust(2, "0") for x in c) for c in colors),
                         image=buf)

    async def register_commands(self):
        await self.bot.wait_until_ready()
        # await manage_commands.remove_all_commands(self.bot.user.id, os.getenv("TOKEN"), None)
        cmds = await manage_commands.get_all_commands(self.bot.user.id, os.getenv("TOKEN"), None)
        print(cmds)
        existing = [cmd["name"] for cmd in cmds]
        for cmd in COMMANDS:
            if cmd not in existing:
                await manage_commands.add_slash_command(self.bot.user.id, os.getenv("TOKEN"), None, cmd,
                                                        COMMANDS[cmd][0], COMMANDS[cmd][1])


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(Slash(bot))
