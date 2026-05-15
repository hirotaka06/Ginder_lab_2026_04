from application.commands.visualize_map import VisualizationCommand
from application.ports.map_renderer import MapRenderer
from domain.boundary.models import JapanBoundaryData
from domain.boundary.repositories import BoundaryRepository
from domain.station.models import Station
from domain.station.repositories import StationRepository
from domain.voronoi.service import VoronoiService


class PrefectureFilterError(Exception):
    """都道府県フィルタリングに失敗したときに送出されるエラー。"""


class VisualizeMapUseCase:
    """ボロノイマップを生成するユースケース。

    - ドメイン層（リポジトリ・サービス）を呼び出してデータを取得・加工
    - 出力ポート（MapRenderer）に描画を委ねる
    """

    def __init__(
        self,
        station_repository: StationRepository,
        boundary_repository: BoundaryRepository,
        voronoi_service: VoronoiService,
        renderer: MapRenderer,
    ) -> None:
        self._station_repository = station_repository
        self._boundary_repository = boundary_repository
        self._voronoi_service = voronoi_service
        self._renderer = renderer

    def execute(self, command: VisualizationCommand) -> None:
        print("観測データを読み込み中...")
        stations = self._station_repository.find_all()

        print("日本の境界データを構築中...")
        boundary = self._boundary_repository.fetch_japan_boundary()

        if command.prefecture:
            boundary, stations = self._apply_prefecture_filter(
                boundary, stations, command.prefecture
            )

        print("ボロノイ図を計算中...")
        voronoi_cells = self._voronoi_service.compute_voronoi_cells(
            stations, boundary.bounds
        )

        self._renderer.render(
            stations=stations,
            voronoi_cells=voronoi_cells,
            boundary=boundary,
            command=command,
        )

    def _apply_prefecture_filter(
        self,
        boundary: JapanBoundaryData,
        stations: list[Station],
        prefecture: str,
    ) -> tuple[JapanBoundaryData, list[Station]]:
        """都道府県境界に絞り込み、境界内の観測所だけを返す。

        Raises:
            PrefectureFilterError: 境界が見つからない、または観測所が0件の場合
        """
        print(f"都道府県フィルタ: {prefecture}")
        try:
            pref_boundary = boundary.filter_by_prefecture(prefecture)
        except Exception as exc:
            raise PrefectureFilterError(str(exc)) from exc

        filtered_stations = pref_boundary.stations_within(stations)
        if not filtered_stations:
            raise PrefectureFilterError(
                f"'{prefecture}' 内に観測データが見つかりません。\n"
                "データセット内の観測所が当該都道府県の外にある可能性があります。"
            )

        print(f"  {len(stations)} 地点 → {len(filtered_stations)} 地点（{prefecture}内）")
        return pref_boundary, filtered_stations
