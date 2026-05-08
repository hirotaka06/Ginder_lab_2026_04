from typing import Protocol

from domain.boundary.models import JapanBoundaryData


class BoundaryRepository(Protocol):
    """地理的境界データの取得インターフェース。"""

    def fetch_japan_boundary(self) -> JapanBoundaryData: ...
