from __future__ import annotations

import urllib.parse
from typing import List

import aiohttp

from ..gmaps import helpers as h


class GeoLocation:
    def __init__(self,
                 key: str):
        self.key = key

    def build_url(self, location: str) -> str:
        location = urllib.parse.quote_plus(location)
        return f"https://maps.googleapis.com/maps/api/geocode/json?" \
               f"address={location}&key={self.key}"

    async def lookup_address(self, address: str) -> List[h.Location]:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(self.build_url(address)) as resp:
                resp.raise_for_status()
                js = await resp.json()
        locations: List[h.Location] = []
        for loc in js["results"]:
            geo = h.LocationGeometry(
                location=h.LocationCoordinates(
                    lat=loc["geometry"]["location"]["lat"],
                    long=loc["geometry"]["location"]["lng"]
                ),
                location_type=loc["geometry"]["location_type"],
                northeast=h.LocationCoordinates(
                    lat=loc["geometry"]["bounds"]["northeast"]["lat"],
                    long=loc["geometry"]["bounds"]["northeast"]["lng"]
                ) if "bounds" in loc["geometry"] else None,
                southwest=h.LocationCoordinates(
                    lat=loc["geometry"]["bounds"]["southwest"]["lat"],
                    long=loc["geometry"]["bounds"]["southwest"]["lng"]
                ) if "bounds" in loc["geometry"] else None,
            )
            comps = [
                h.LocationComponent(
                    long=comp["long_name"],
                    short=comp["short_name"],
                    type=comp["types"]
                )
                for comp in loc["address_components"]
            ]
            locations.append(
                h.Location(
                    address_components=comps,
                    formatted_address=loc["formatted_address"],
                    geometry=geo
                )
            )
        return locations
