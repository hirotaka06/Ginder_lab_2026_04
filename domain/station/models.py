from dataclasses import dataclass

from domain.station.errors import InvalidCoordinateError


@dataclass(frozen=True)
class Coordinate:
    """緯度・経度を表す値オブジェクト。

    frozen=True により不変（イミュータブル）です。
    同じ座標は同一のオブジェクトとして扱われます。
    """

    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90 <= self.lat <= 90):
            raise InvalidCoordinateError
        if not (-180 <= self.lon <= 180):
            raise InvalidCoordinateError


@dataclass
class Station:
    """観測所を表すエンティティ。

    観測所は「座標」と「計測値」を持ちます。
    """

    coordinate: Coordinate
    measurement_value: float
    name: str | None = None

    @property
    def lat(self) -> float:
        return self.coordinate.lat

    @property
    def lon(self) -> float:
        return self.coordinate.lon
