from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LocationComponent:
    short: str
    long: str
    type: List[str]


@dataclass(frozen=True)
class LocationCoordinates:
    lat: float
    long: float


@dataclass(frozen=True)
class LocationGeometry:
    northeast: LocationCoordinates
    southwest: LocationCoordinates
    location: LocationCoordinates
    location_type: str


@dataclass(frozen=True)
class Location:
    address_components: List[LocationComponent]
    formatted_address: str
    geometry: LocationGeometry
