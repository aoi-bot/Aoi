import asyncio
import logging
import os
import sys

import discord
import dotenv
from discord.ext import commands

import aoi

os.chdir(os.path.dirname(sys.argv[0]))
logging.basicConfig(level=logging.INFO)
logging.addLevelName(15, "BDBG")
dotenv.load_dotenv(".env")


def get_prefix(_bot: aoi.AoiBot, message: discord.Message):
    if message.guild.id not in _bot.db.prefixes:
        asyncio.create_task(_bot.db.guild_setting(message.guild.id))
        return commands.when_mentioned_or(",")(_bot, message)
    return commands.when_mentioned_or(_bot.db.prefixes[message.guild.id])(_bot, message)


bot = aoi.AoiBot(command_prefix=get_prefix, help_command=None)

extensions = {
    "Administration": {
        # administration cogs
        "cogs.administration.aoi": "Aoi",
        "cogs.administration.information": "Information",
        "cogs.administration.roles": "Roles",
        "cogs.administration.guild": "Guilds",
        "cogs.administration.permissions": "Permissions"
    },
    "Misc": {

        # misc/fun cogs
        "cogs.colors": "Colors",
        "cogs.nsfw": "NSFW",
        "cogs.math": "Math",
        "cogs.messages": "Messages",
        # "cogs.geolocation",
        # " cogs.nasa",
        # "cogs.weather",
        "cogs.searches": "Searches"
    },
    "Profile/Currency": {

        # user/currency cogs
        "cogs.user.xp": "XP",
        "cogs.user.profile": "Profile",
        "cogs.user.currency": "Currency",
        "cogs.user.global_shop": "GlobalShop",
        "cogs.user.guild_shop": "ServerShop",
        "cogs.user.guild_gambling": "ServerGambling",
    },
    "Utility/Config": {

        # utility and config cogs
        "cogs.errorhandler": "ErrorHandler",
        "cogs.settings.guildsettings": "GuildSettings",
        "cogs.help": "Help"
    }
}

for grp_name, ext_set in extensions.items():
    for path, cog_name in ext_set.items():
        logging.info(f"cog:Loading {grp_name}:{cog_name} from {path}")
        bot.load_extension(path)
        bot.set_cog_group(cog_name, grp_name)


@bot.event
async def on_ready():
    logging.info("Bot online!")
    await bot.change_presence(activity=discord.Game("Hello :)"))


@bot.check
async def permission_check(ctx: aoi.AoiContext):
    can_use = True
    current_n = 0

    def update_use(can: bool, _n: int):
        nonlocal current_n
        nonlocal can_use
        can_use = can
        if not can:
            current_n = _n

    if ctx.command.name == 'help':
        return True

    if ctx.command.cog.qualified_name == "Permissions":
        return True
    perms = await bot.db.get_permissions(ctx.guild.id)
    for n, i in enumerate(perms):
        tok = i.split()
        if tok[0] == "asm":
            update_use(tok[1] == "enable", n)
        if tok[0] == "acm":
            if ctx.channel.id == int(tok[1]):
                update_use(tok[2] == "enable", n)
        if tok[0] == "cm":
            if ctx.channel.id == int(tok[1]) and \
                    ctx.command.cog.qualified_name.lower() == tok[3].lower():
                update_use(tok[2] == "enable", n)
        if tok[0] == "sc":
            if ctx.command.name.lower() == tok[1].lower():
                update_use(tok[2] == "enable", n)
        if tok[0] == "sm":
            if ctx.command.cog.qualified_name.lower() == tok[1].lower():
                update_use(tok[2] == "enable", n)
    if not can_use:
        raise aoi.PermissionFailed(f"Permission #{current_n} - {perms[current_n]} "
                                   f"is disallowing you from this command")
    return True


bot.run(os.getenv("TOKEN"))
