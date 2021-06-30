from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING, Union

import discord
from libs.converters import AoiColor

if TYPE_CHECKING:
    from bot.aoi import AoiContext

num_list = "zero,one,two,three,four,five,six,seven,eight,nine".split(",")


def discord_number_emojis(num: int):
    return "".join(f":{num_list[int(n)]}:" for n in str(num))


def color_to_string(color: Union[discord.Color, AoiColor]) -> str:
    return "".join(hex(n)[2:].rjust(2, "0") for n in color.to_rgb())


def hex_color_to_string(color: int) -> str:
    return hex(color)[2:].rjust(6, "0")


def dhm_notation(td: timedelta, sep="", full=False):
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    return sep.join([f"{td.days}{'days' if full else 'd'}",
                     f"{hours}{'hours' if full else 'h'}",
                     f"{minutes}{'minutes' if full else 'm'}"])


def hms_notation(seconds: Union[int, timedelta]):
    if isinstance(seconds, timedelta):
        seconds = seconds.total_seconds()
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h{minutes}m{seconds}s"


def dhms_notation(delta: Union[int, timedelta]):
    if isinstance(delta, int):
        delta = timedelta(seconds=delta)
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{delta.days}d{hours}h{minutes}m{seconds}s"


def camel_to_title(camel: str):
    return camel.replace("_", " ").title()


def escape(text: str, ctx: Union[AoiContext, discord.Message]):
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


def maybe_pluralize(count: int, word: str, word_pl: str, *, number_format="") -> str:
    return number_format % count + (word if count == 1 else word_pl)


def sql_trim(sql: str) -> str:
    if sql.startswith("```sql") and sql.endswith("```"):
        return sql[6:-3]
    if sql.startswith("```") and sql.endswith("```"):
        return sql[3:-3]
    if sql.startswith("`") and sql.endswith("`"):
        return sql[1:-1]
    return sql
