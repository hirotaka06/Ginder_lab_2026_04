import csv

from domain.models import StationRecord


class CSVDataLoader:
    """CSV フォーマット（ヘッダー必須）: name,lat,lon,<value_column>"""

    def __init__(self, csv_path: str, value_column: str = "value") -> None:
        self.csv_path = csv_path
        self.value_column = value_column

    def load(self) -> list[StationRecord]:
        records: list[StationRecord] = []
        with open(self.csv_path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                records.append(
                    StationRecord(
                        name=row["name"],
                        lat=float(row["lat"]),
                        lon=float(row["lon"]),
                        value=float(row[self.value_column]),
                    )
                )
        return records
