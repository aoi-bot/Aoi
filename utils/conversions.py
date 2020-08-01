import discord


def color_to_string(color: discord.Color):
    return "".join(hex(n)[2:] for n in color.to_rgb())
