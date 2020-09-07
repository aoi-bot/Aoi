from datetime import timedelta

import discord


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
