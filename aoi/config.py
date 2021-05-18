from __future__ import annotations

from abc import ABC
from typing import Any, Dict, List, Tuple

from ruamel.yaml import YAML, os

class ConfigHandler:
    def __init__(self):
        if not os.path.isfile("assets/config.yaml"):
            with open("assets/config_sample.yaml") as sample, open("assets/config.yaml", "w") as config:
                config.write(sample.read())
        with open("assets/config.yaml") as config:
            self.yaml = YAML().load(config)

    def save(self):
        with open("assets/config.yaml", "w") as fp:
            YAML().dump(self.yaml, fp)

    def get(self, key: str) -> Any:
        if key not in self.all_keys():
            raise ValueError
        return self.yaml[key.split(".")[0]][key.split(".")[1]]

    def set(self, key: str, value: Any) -> None:
        if key not in self.all_keys():
            raise ValueError
        self.yaml[key.split(".")[0]][key.split(".")[1]] = type(self.get(key))(value)
        self.save()

    def all_keys(self) -> List[str]:
        keys = []
        for category in self.yaml:
            for key, value in self.yaml[category].items():
                keys.append(f"{category}.{key}")
        return keys

    def all_keys_in(self, category: str) -> List[Tuple[str, Any]]:
        keys = []
        if category not in self.yaml:
            raise ValueError
        for key, value in self.yaml[category].items():
            keys.append((key, value))
        return keys
