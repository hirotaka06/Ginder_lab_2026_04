from dataclasses import dataclass, field

from shapely.geometry import Point

from domain.boundary.errors import BoundaryLoadError


@dataclass(frozen=True)
class JapanBoundaryData:
    """日本の地理的境界を表す値オブジェクト。

    Attributes:
        outline:          日本全体を結合した1つの境界ポリゴン（Shapely geometry）
        prefectures:      都道府県ごとの境界ポリゴンのリスト（Shapely geometry リスト）
        prefecture_names: 各都道府県の日本語名（prefectures と同じ順序）
    """

    outline: object
    prefectures: list[object] = field(default_factory=list)
    prefecture_names: list[str] = field(default_factory=list)

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """地図の表示範囲を (minx, miny, maxx, maxy) で返す。"""
        return self.outline.bounds

    def filter_by_prefecture(self, name: str) -> "JapanBoundaryData":
        """指定した都道府県名のみの境界データを返す。

        Args:
            name: 都道府県名（例: "茨城県", "北海道"）

        Raises:
            BoundaryLoadError: 指定した都道府県が見つからない場合
        """
        matched_geoms = [
            geom
            for geom, pref_name in zip(self.prefectures, self.prefecture_names)
            if pref_name == name
        ]
        if not matched_geoms:
            available = ", ".join(self.prefecture_names)
            raise BoundaryLoadError(
                f"都道府県 '{name}' が見つかりません。\n"
                f"利用可能な名前の例: {available[:80]}…"
            )
        pref_polygon = matched_geoms[0]
        return JapanBoundaryData(
            outline=pref_polygon,
            prefectures=[pref_polygon],
            prefecture_names=[name],
        )

    def stations_within(self, stations: list, tolerance_deg: float = 0.02) -> list:
        """指定した境界内にある観測所だけを返す。

        Args:
            stations:      Station のリスト
            tolerance_deg: 境界線上の観測所を拾うためのバッファ（度）。
                           0.02° ≒ 約 2 km
        """
        buffered = self.outline.buffer(tolerance_deg)
        return [s for s in stations if buffered.contains(Point(s.lon, s.lat))]
