import csv
import io
from pathlib import Path

from domain.station.errors import StationDataError
from domain.station.models import Coordinate, Station


class CSVStationRepository:
    """CSVファイルから観測所データを取得する

    CSVの列構成例:
        name, lat, lon, value
    """

    def __init__(self, csv_path: str, value_column: str = "value") -> None:
        self._csv_path = csv_path
        self._value_column = value_column

    def find_all(self) -> list[Station]:
        text = Path(self._csv_path).read_text(encoding="utf-8")
        stations = []
        for row in csv.DictReader(io.StringIO(text)):
            station = self._row_to_station_or_none(row)
            if station is not None:
                stations.append(station)
        if not stations:
            raise StationDataError
        return stations

    def _row_to_station_or_none(self, row: dict) -> "Station | None":
        """行を Station に変換する。値が欠損している行は None を返す。"""
        try:
            value_str = row.get(self._value_column, "")
            if not value_str or value_str.strip() in ("", "nan", "None"):
                return None
            return Station(
                coordinate=Coordinate(
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                ),
                measurement_value=float(value_str),
                name=row.get("name"),
            )
        except (KeyError, ValueError):
            return None
