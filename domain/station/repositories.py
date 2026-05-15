from typing import Protocol

from domain.station.models import Station


class StationRepository(Protocol):
    """観測所データの取得インターフェース。
    """

    def find_all(self) -> list[Station]: ...
