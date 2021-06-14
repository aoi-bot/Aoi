import asyncio

import aoi
from discord.ext import commands


# TODO help refactor

class TaskManagement(commands.Cog):
    def __init__(self, bot: aoi.AoiBot):
        self.bot = bot

    @property
    def description(self) -> str:
        return "Manage your running tasks"

    @commands.command(
        brief="List your active tasks"
    )
    async def mytasks(self, ctx: aoi.AoiContext):
        if ctx.author in self.bot.tasks and self.bot.tasks[ctx.author]:
            return await ctx.paginate(self.bot.tasks[ctx.author], 5, "Your running tasks", numbered=True)
        await ctx.send_info("You have no running tasks")

    @commands.is_owner()
    @commands.command(brief="Starts a long task")
    async def longtask(self, ctx: aoi.AoiContext):
        n = 0

        async def do_op():
            nonlocal n
            while True:
                await asyncio.sleep(1)
                n += 1

        await self.bot.create_task(ctx, do_op(), lambda: f"at {n}")

    @commands.command(
        brief="Stops an active task. Defaults to previous task"
    )
    async def stoptask(self, ctx: aoi.AoiContext, num: int = -1):
        if ctx.author not in self.bot.tasks or not self.bot.tasks[ctx.author]:
            return await ctx.send_info("You have no running tasks")
        if num < -1 or num >= len(self.bot.tasks[ctx.author]):
            return await ctx.send_error(f"Invalid task, do `{ctx.prefix}mytasks` to see your tasks.")
        task = self.bot.tasks[ctx.author][num]
        await ctx.send_ok("Cancel task?\n" + str(task) + "\n`yes` or `cancel`")
        conf = await ctx.input(str, ch=lambda m: m.lower() in ["yes"])
        if not conf:
            return await ctx.send_ok("Cancellation stopped")
        task.task.cancel()
        await ctx.send_ok("Task stopped")


def setup(bot: aoi.AoiBot) -> None:
    bot.add_cog(TaskManagement(bot))
