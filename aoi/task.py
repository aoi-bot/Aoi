import asyncio
import logging
from dataclasses import dataclass

import discord
from discord.ext import commands


class AoiTask:
    def __init__(self, task: asyncio.Task, ctx: commands.Context):
        self.task = task
        self.ctx = ctx
        logging.info(f"Creating task for {ctx.author.id} {ctx.message.content}")

    def __del__(self):
        logging.info(f"Deleting task for {self.ctx.author.id} {self.ctx.message.content}")

    @property
    def member(self) -> discord.Member:
        return self.ctx.author

    def guild(self) -> discord.Guild:
        return self.ctx.guild
