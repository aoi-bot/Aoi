from dataclasses import dataclass
from datetime import datetime


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
