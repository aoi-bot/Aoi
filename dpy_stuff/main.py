import multiprocessing
import sys

try:
    sys.path.append(sys.argv[0])
except:  # noqa
    sys.path.append(sys.argv[1])

import asyncio
import logging
import os
import traceback

import discord
import dotenv
from discord.ext import commands

from aoi import bot

try:
    os.chdir(os.path.dirname(sys.argv[0]))
except FileNotFoundError:
    pass
except OSError:  # fuck windows
    pass

logging.addLevelName(7, "TRACE")

dotenv.load_dotenv(".env")


def get_prefix(_bot: bot.AoiBot, message: discord.Message):
    if not message.guild:
        return commands.when_mentioned_or(",")(_bot, message)
    if message.guild.id not in _bot.db.prefixes:
        asyncio.create_task(_bot.db.guild_setting(message.guild.id))
        return commands.when_mentioned_or(",")(_bot, message)
    return commands.when_mentioned_or(_bot.db.prefixes[message.guild.id])(_bot, message)


bot = bot.AoiBot(
    command_prefix=get_prefix,
    help_command=None,
    intents=discord.Intents.all(),
    fetch_offline_users=True,
    chunk_members_on_startup=True,
)

bot.load_extensions()


@bot.check
async def permission_check(ctx: bot.AoiContext):  # noqa: C901
    if not ctx.guild:
        return True
    can_use = True
    current_n = 0

    if ctx.author.id in ctx.bot.db.blacklisted:
        return

    def update_use(can: bool, _n: int):
        nonlocal current_n
        nonlocal can_use
        can_use = can
        if not can:
            current_n = _n

    if ctx.command.name == "help":
        return True

    if ctx.command.cog.qualified_name == "Permissions":
        return True
    perms = await bot.db.get_permissions(ctx.guild.id)
    roles = [r.id for r in ctx.author.roles]
    channel = ctx.channel.id
    category = ctx.channel.category.id if ctx.channel.category else 0
    command_name = ctx.command.name.lower()
    cog_name = ctx.command.cog.qualified_name.lower()
    user = ctx.author.id
    for n, i in enumerate(perms):
        tok = i.split()

        if tok[0] == "asm":
            update_use(tok[1] == "enable", n)
        if tok[0] == "acm":
            if channel == int(tok[1]):
                update_use(tok[2] == "enable", n)
        if tok[0] == "arm" and int(tok[1]) in roles:
            update_use(tok[1] == "enable", n)
        if tok[0] == "axm" and int(tok[1]) == category:
            update_use(tok[2] == "enable", n)
        if tok[0] == "aum" and int(tok[1]) == user:
            update_use(tok[2] == "enable", n)

        if tok[0] == "cm":
            if ctx.channel.id == int(tok[1]) and cog_name.lower() == tok[3].lower():
                update_use(tok[2] == "enable", n)
        if tok[0] == "sm":
            if cog_name.lower() == tok[2].lower():
                update_use(tok[1] == "enable", n)
        if tok[0] == "xm":
            if cog_name.lower() == tok[3].lower() and category == int(tok[1]):
                update_use(tok[2] == "enable", n)
        if tok[0] == "rm":
            if cog_name.lower() == tok[3].lower() and int(tok[1]) in roles:
                update_use(tok[2] == "enable", n)
        if tok[0] == "um":
            if cog_name.lower() == tok[3].lower() and int(tok[1]) == user:
                update_use(tok[2] == "enable", n)

        if tok[0] == "cc":
            if ctx.channel.id == int(tok[1]) and command_name.lower() == tok[3].lower():
                update_use(tok[2] == "enable", n)
        if tok[0] == "sc":
            if command_name.lower() == tok[2].lower():
                update_use(tok[1] == "enable", n)
        if tok[0] == "xc":
            if command_name.lower() == tok[3].lower() and category == int(tok[1]):
                update_use(tok[2] == "enable", n)
        if tok[0] == "rc":
            if command_name.lower() == tok[3].lower() and int(tok[1]) in roles:
                update_use(tok[2] == "enable", n)
        if tok[0] == "rc":
            if command_name.lower() == tok[3].lower() and int(tok[1]) == user:
                update_use(tok[2] == "enable", n)
    if not can_use:
        raise bot.PermissionFailed(
            f"Permission #{current_n} - {perms[current_n]} "
            f"is disallowing you from this command"
        )
    return True


dashboard = Dashboard(bot)


def bot_process():
    try:
        bot.logger.info(f"Starting Aoi Bot with PID {os.getpid()}")
        bot.run(os.getenv("TOKEN"))
    except Exception as error:
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )
        exit(1)


def dashboard_process():
    dashboard.run()


_bot_proc = multiprocessing.Process(target=bot_process)
_dash_proc = multiprocessing.Process(target=dashboard_process)

_bot_proc.start()
_dash_proc.start()

_bot_proc.join()
_dash_proc.kill()

if bot.is_restarting:
    os.execl(sys.executable, sys.executable, *sys.argv)
