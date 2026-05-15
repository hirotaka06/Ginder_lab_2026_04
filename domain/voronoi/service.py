import numpy as np
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.geometry import box as shapely_box
from shapely.ops import voronoi_diagram

from domain.station.models import Station
from domain.voronoi.errors import VoronoiComputationError

_CLIP_MARGIN = 15.0


class VoronoiService:
    """ボロノイ図の計算を担うサービス。

    ボロノイ図とは「各観測所に最も近い領域」を平面分割した図です。
    """

    def compute_voronoi_cells(
        self,
        stations: list[Station],
        boundary_bounds: tuple[float, float, float, float],
    ) -> list[Polygon]:
        """各観測所に対応するボロノイ領域を返す。

        Args:
            stations: 観測所のリスト
            boundary_bounds: 計算範囲の (minx, miny, maxx, maxy)

        Returns:
            stations と同じ順序で対応するボロノイ領域のリスト

        Raises:
            VoronoiComputationError: ボロノイ計算中に例外が発生した場合
        """
        try:
            clip_box = self._build_clip_box(boundary_bounds)
            points = np.array([[st.lon, st.lat] for st in stations])
            regions = voronoi_diagram(MultiPoint(points), envelope=clip_box)
            return [
                min(regions.geoms, key=lambda r: r.distance(Point(pt)))
                for pt in points
            ]
        except Exception as exc:
            raise VoronoiComputationError from exc

    def _build_clip_box(
        self,
        bounds: tuple[float, float, float, float],
    ) -> Polygon:
        """ボロノイ計算用の切り抜き矩形を構築する。"""
        minx, miny, maxx, maxy = bounds
        return shapely_box(
            minx - _CLIP_MARGIN,
            miny - _CLIP_MARGIN,
            maxx + _CLIP_MARGIN,
            maxy + _CLIP_MARGIN,
        )
