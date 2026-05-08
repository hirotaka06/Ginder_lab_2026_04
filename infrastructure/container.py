from adapters.presenters.map_plotter import MapPlotter
from adapters.repositories.csv_station_repository import CSVStationRepository
from adapters.repositories.geojson_boundary_repository import GeoJSONBoundaryRepository
from application.use_cases.visualize_map import VisualizeMapUseCase
from domain.voronoi.service import VoronoiService
from infrastructure.settings import GEOJSON_PATH


def build_visualize_map_use_case(
    csv_path: str,
    value_column: str,
) -> VisualizeMapUseCase:
    return VisualizeMapUseCase(
        station_repository=CSVStationRepository(
            csv_path, value_column=value_column),
        boundary_repository=GeoJSONBoundaryRepository(GEOJSON_PATH),
        voronoi_service=VoronoiService(),
        renderer=MapPlotter(),
    )
