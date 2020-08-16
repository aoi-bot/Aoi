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
