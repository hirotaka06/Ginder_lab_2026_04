from typing import Protocol

from domain.models import StationRecord


class DataLoader(Protocol):
    def load(self) -> list[StationRecord]: ...
