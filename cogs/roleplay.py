import random
from dataclasses import dataclass
from typing import List, Dict, Tuple

import aiohttp
from ruamel.yaml import YAML

import aoi
import discord
from discord.ext import commands


class Roleplay(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot
        self.custom_reactions: Dict[str, CustomReaction] = {}
        self.roleplay_responses: Dict[str, RoleplayResponse] = {}

    @property
    def description(self) -> str:
        return "Roleplay commands"


def setup(bot: aoi.AoiBot) -> None:
    fun = Roleplay(bot)

    bot.add_cog(fun)

    async def get_data(name) -> Tuple[RoleplayResponse, str]:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"https://api.waifu.pics/sfw/{name}") as resp:
                return fun.roleplay_responses[name], (await resp.json())["url"]

    async def exec_multi_rp_command(self: Roleplay, ctx: aoi.AoiContext, user: discord.Member):
        resp, image = await get_data(ctx.command.name)
        await ctx.embed(
            description=random.choice(resp.phrases).format(f"**{ctx.author.display_name}**",
                                                           f"**{user.display_name}**"),
            image=image
        )

    async def exec_single_rp_command(self: Roleplay, ctx: aoi.AoiContext):
        resp, image = await get_data(ctx.command.name)
        await ctx.embed(
            description=random.choice(resp.phrases).format(f"**{ctx.author.display_name}**"),
            image=image
        )

    with open("loaders/roleplay.yaml") as fp:
        doc = YAML().load(fp)
        for key in doc:
            if doc[key]["enabled"] == "no":
                continue

            fun.roleplay_responses[key] = RoleplayResponse(doc[key]["multi"] == "yes", doc[key]["phrases"])

            cmd = commands.Command(
                name=key,
                func=exec_multi_rp_command if fun.roleplay_responses[key].multi else exec_single_rp_command,
                brief=f"{key} someone" if fun.roleplay_responses[key].multi else f"{key} roleplay command"
            )

            cmd.cog = fun
            fun.bot.add_command(cmd)
            fun.__cog_commands__ += (cmd,)


@dataclass
class CustomReaction:
    responses: List[str]
    images: List[str]


@dataclass
class RoleplayResponse:
    multi: bool
    phrases: List[str]