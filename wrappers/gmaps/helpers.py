from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LocationComponent:
    short: str
    long: str
    type: List[str]


@dataclass(frozen=True)
class LocationCoordinates:
    lat: float
    long: float

    def __str__(self):
        return f"{self.lat:.6}°{'N' if self.lat > 0 else 'S'} " \
               f"{self.long:.6}°{'E' if self.long > 0 else 'W'} "


@dataclass(frozen=True)
class LocationGeometry:
    northeast: Optional[LocationCoordinates]
    southwest: Optional[LocationCoordinates]
    location: LocationCoordinates
    location_type: str


@dataclass(frozen=True)
class Location:
    address_components: List[LocationComponent]
    formatted_address: str
    geometry: LocationGeometry
