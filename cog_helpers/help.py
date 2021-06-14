import re
from typing import Tuple, Optional

from aoi import AoiContext
from discord.ext.commands import Command


# noinspection PyMethodMayBeStatic
class HelpCogService:
    def get_command_signature(self, cmd: Command, ctx: AoiContext):

        return f"`{ctx.clean_prefix}{cmd.name} " + (
            cmd.usage or
            f"{re.sub(r'[<>]', '', cmd.signature) if cmd.signature else ''}{' [flags]' if cmd.flags else ''}") + "`"

    def format_flag(self, flag_tup: Tuple[str, Tuple[Optional[type], str]]) -> str:
        if flag_tup[1][0]:
            return f"⋄ `--{flag_tup[0]} {flag_tup[1][0].__name__}` - {flag_tup[1][1]}"
        else:
            return f"⋄ `--{flag_tup[0]}` - {flag_tup[1][1]}"
