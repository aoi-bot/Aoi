from typing import Any, List, Union


def arrows_from_direction(direction: str):
    if len(direction) == 3:
        direction = direction[1:]
    return {
        "N": "↓",
        "NE": "↙",
        "E": "←",
        "SE": "↖",
        "S": "↑",
        "SW": "↗",
        "W": "→",
        "NW": "↘"
    }[direction.upper()]


def arg_or_0_index(arg: Union[List[Any], Any]) -> Any:
    if isinstance(arg, list):
        return arg[0]
    else:
        return arg
