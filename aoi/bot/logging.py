import logging

from colorama import Fore, Style, init

init()

colors = {
    "TRACE": f"{Fore.WHITE}{Style.DIM}",
    "TRACE_HIKARI": f"{Fore.WHITE}{Style.DIM}",
    "DEBUG": f"{Fore.LIGHTWHITE_EX}",
    "INFO": "",
    "WARNING": f"{Fore.YELLOW}{Style.BRIGHT}",
    "ERROR": f"{Fore.LIGHTRED_EX}{Style.BRIGHT}",
    "CRITICAL": f"{Fore.RED}{Style.BRIGHT}",
}
colors2 = {
    "TRACE": f"{Fore.WHITE}{Style.DIM}",
    "TRACE_HIKARI": f"{Fore.WHITE}{Style.DIM}",
    "DEBUG": Fore.LIGHTWHITE_EX,
    "INFO": Fore.BLUE,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.LIGHTRED_EX,
    "CRITICAL": Fore.RED,
}
styles = {
    "TRACE": f"{Fore.WHITE}{Style.DIM}",
    "TRACE_HIKARI": f"{Fore.WHITE}{Style.DIM}",
    "DEBUG": f"{Fore.LIGHTWHITE_EX}",
    "INFO": "",
    "WARNING": "",
    "ERROR": "",
    "CRITICAL": Style.BRIGHT,
}
color_patterns = {
    "yougan": Fore.GREEN,
    "hikari.bot": Fore.MAGENTA,
    "hikari.gateway": Fore.MAGENTA,
    "discord.http": Fore.RED,
    "": Fore.YELLOW,
}

color_patterns_cache: dict[str, str] = {"": Fore.YELLOW}

ignored: dict[str, list[str]] = {}


class LoggingHandler(logging.Logger):
    def handle(self, record: logging.LogRecord) -> None:
        if record.msg in ignored.get(record.name, ()):
            return
        name = record.name
        level = record.levelno  # noqa F841
        level_name = record.levelname
        message = record.msg % record.args

        print(
            f"{colors2[level_name]}{styles[level_name]}{level_name:>8}{Style.RESET_ALL}"
            f" "
            f"{Style.BRIGHT}{self._get_color(name)}{name}{Style.RESET_ALL} " + f"» "
            f"{colors[level_name]}{message}{Style.RESET_ALL}"
        )

    # noinspection PyMethodMayBeStatic
    def _get_color(self, name: str) -> str:
        if name in color_patterns_cache:
            return color_patterns_cache[name]
        for nm, color in color_patterns.items():
            if name.startswith(nm):
                color_patterns_cache[name] = color
                return color
        return color_patterns[""]
