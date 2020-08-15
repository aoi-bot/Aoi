from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import wrappers.gmaps as gmaps

from dataclasses import dataclass


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
