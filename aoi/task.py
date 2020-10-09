import asyncio
import logging
from datetime import datetime
from typing import Callable

import discord
from discord.ext import commands


class AoiTask:
    def __init__(self, task: asyncio.Task, ctx: commands.Context, status: Callable[[], str]):
        self.task = task
        self.ctx = ctx
        self._status = status
        self.time = datetime.now()
        self.bot.logger.info(f"Creating task for {ctx.author.id} {ctx.message.content}")

    def __del__(self):
        self.bot.logger.info(f"Deleting task for {self.ctx.author.id} {self.ctx.message.content}")

    def __str__(self) -> str:
        return f"{self.member.mention} {self.time.strftime('%x %X')} [Jump]({self.message.jump_url})\n" \
               + (self.status + "\n" or "") + \
               f"{self.message.content}\n"

    @property
    def status(self) -> str:
        return self._status()

    @property
    def message(self) -> discord.Message:
        return self.ctx.message

    @property
    def member(self) -> discord.Member:
        return self.ctx.author

    def guild(self) -> discord.Guild:
        return self.ctx.guild
