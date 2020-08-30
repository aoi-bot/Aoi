from datetime import datetime
from typing import Dict, Tuple, List

import aiohttp

from wrappers import gmaps
from .helpers import LatLongLookupResult, WeatherCondition


class WeatherGov:
    def __init__(self, key: str):
        self.key = key
        self.grid_cache: Dict[Tuple[float, float], LatLongLookupResult] = {}

    async def lookup_grid(self, lat: float, long: float) -> \
            LatLongLookupResult:
        lat = round(lat, 4)
        long = round(long, 4)
        if (lat, long) in self.grid_cache:
            return self.grid_cache[(lat, long)]
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"https://api.weather.gov/points/{lat},{long}") as resp:
                js = await resp.json()
                js = js["properties"]
        result = LatLongLookupResult(
            point=gmaps.LocationCoordinates(
                lat=lat,
                long=long
            ),
            grid_x=js["gridX"],
            grid_y=js["gridY"],
            forecast_grid_data_endpoint=js["forecastGridData"],
            forecast_hourly_endpoint=js["forecastHourly"],
            forecast_endpoint=js["forecast"],
            time_zone=js["timeZone"],
            radar_station=js["radarStation"],
        )
        self.grid_cache[(lat, long)] = result
        return result

    async def lookup_hourly(self, location: gmaps.LocationCoordinates) -> \
            List[WeatherCondition]:
        grid = await self.lookup_grid(location.lat, location.long)
        async with aiohttp.ClientSession() as sess:
            async with sess.get(grid.forecast_hourly_endpoint) as resp:
                js = (await resp.json())["properties"]["periods"]
        return [
            WeatherCondition(
                start=datetime.fromisoformat(wc["startTime"]),
                end=datetime.fromisoformat(wc["endTime"]),
                is_day=wc["isDaytime"],
                temp=wc["temperature"],
                temp_unit=wc["temperatureUnit"],
                wind=wc["windSpeed"].split()[0],
                wind_unit=wc["windSpeed"].split()[1],
                wind_direction=wc["windDirection"],
                icon=wc["icon"],
                short_forecast=wc["shortForecast"]
            )
            for wc in js
        ]
