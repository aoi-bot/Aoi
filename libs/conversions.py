from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from aoi import AoiContext

num_list = "zero,one,two,three,four,five,six,seven,eight,nine".split(",")

def discord_number_emojis(num: int):
    return "".join(f":{num_list[int(n)]}:" for n in str(num))

def color_to_string(color: discord.Color) -> str:
    return "".join(hex(n)[2:] for n in color.to_rgb())


def hex_color_to_string(color: int) -> str:
    return hex(color)[2:].rjust(6, "0")


def dhm_notation(td: timedelta, sep="", full=False):
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    return sep.join([f"{td.days}{'days' if full else 'd'}",
                     f"{hours}{'hours' if full else 'h'}",
                     f"{minutes}{'minutes' if full else 'm'}"])


def hms_notation(seconds: int):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h{minutes}m{seconds}s"


def camel_to_title(camel: str):
    return camel.replace("_", " ").title()


def escape(text: str, ctx: AoiContext):
    role_mentions = re.findall(r"<@&\d{17,21}>", text)
    for mention in role_mentions:
        role = ctx.guild.get_role(int(mention[3:-1]))
        text = text.replace(mention, f"@{role.name}" if role else mention)
    user_mentions = re.findall(r"<@!?\d{17,21}>", text)
    for mention in user_mentions:
        user = ctx.guild.get_member(int(mention.replace('!', '')[2:-1]))
        text = text.replace(mention, f"@{user.name}" if user else mention)
    channel_mentions = re.findall(r"<#\d{17,21}>", text)
    for mention in channel_mentions:
        print(mention)
        channel = ctx.guild.get_channel(int(mention[2:-1]))
        text = text.replace(mention, f"#{channel.name}" if channel else mention)
    return text
