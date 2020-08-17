from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import wrappers.gmaps as gmaps

from dataclasses import dataclass
from libs.misc import arrows_from_direction

@dataclass(frozen=True)
class LatLongLookupResult:
    point: gmaps.LocationCoordinates
    grid_x: int
    grid_y: int
    forecast_endpoint: str
    forecast_hourly_endpoint: str
    forecast_grid_data_endpoint: str
    time_zone: str
    radar_station: str


@dataclass(frozen=True)
class WeatherCondition:
    start: datetime.datetime
    end: datetime.datetime
    is_day: bool
    temp: int
    temp_unit: str
    wind: int
    wind_unit: str
    wind_direction: str
    icon: str
    short_forecast: str

    def line(self):
        return f"{self.start.strftime('%m-%d %H:%M'):>7}{'D' if self.is_day else 'N'} {self.temp:>4}°{self.temp_unit} " \
               f"{str(self.wind) + self.wind_unit:>10} {self.wind_direction:>3}" \
               f"{arrows_from_direction(self.wind_direction)}"
