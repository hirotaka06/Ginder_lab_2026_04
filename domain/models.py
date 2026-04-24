from dataclasses import dataclass


@dataclass
class StationRecord:
    name: str
    lat: float
    lon: float
    value: float
