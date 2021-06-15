from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class GuildSettingModel:
    ok_color: int
    error_color: int
    info_color: int
    perm_errors: bool
    currency_img: str
    currency_chance: int
    currency_max: int
    currency_min: int
    currency_gen_channels: List[int]
    delete_on_ban: bool
    reply_embeds: bool


@dataclass(frozen=True)
class RoleShopItemModel:
    type: str
    data: str
    cost: int


@dataclass(frozen=True)
class PunishmentModel:
    user: int
    guild: int
    staff: int
    typ: int
    reason: str
    time: datetime
    cleared: int
    cleared_by: int


class PunishmentTypeModel:
    BAN = 0
    KICK = 1
    MUTE = 2
    WARN = 3
    UNBAN = 4
    SOFTBAN = 5


@dataclass()
class TimedPunishmentModel:
    _id: int
    guild: int
    role: int
    end: int
    ismute: bool
    user: int


@dataclass()
class AoiMessageModel:
    message: str
    channel: int
    delete: int