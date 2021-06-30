from dataclasses import dataclass
from sqlite3 import Row
from typing import List


class GuildSettingModel:
    def __init__(self, ok_color: int = 0x00aa00,
                 error_color: int = 0xaa0000,
                 info_color: int = 0x0000aa,
                 perm_errors: bool = True,
                 currency_img: str = "",
                 currency_chance: int = 4,
                 currency_max: int = 8,
                 currency_min: int = 10,
                 currency_gen_channels: List[int] = [],  # noqa
                 delete_on_ban: bool = False,
                 reply_embeds: bool = True):
        self.colors = _GuildSettingColorModel(ok_color, error_color, info_color)

        self.perm_errors = perm_errors
        self.currency_img = currency_img
        self.currency_chance = currency_chance
        self.currency_max = currency_max
        self.currency_min = currency_min
        self.currency_gen_channels = currency_gen_channels
        self.delete_on_ban = delete_on_ban
        self.reply_embeds = reply_embeds

    @property
    def ok_color(self):
        return self.colors.ok

    @property
    def error_color(self):
        return self.colors.error

    @property
    def info_color(self):
        return self.colors.info

    @classmethod
    def from_row(cls, row: Row):
        return cls(
            int(row[1], 16),
            int(row[2], 16),
            int(row[3], 16),
            row[5], row[6],
            int(row[7]),
            int(row[8]),
            int(row[9]),
            [int(x) for x in row[10].split(",")] if row[10] else [],
            row[11] == 1, row[12] == 1
        )


@dataclass
class _GuildSettingColorModel:
    ok: int
    error: int
    info: int


@dataclass
class _GuildSettingCurrencyModel:
    img: str
    chance: int
