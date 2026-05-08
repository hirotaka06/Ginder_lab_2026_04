from typing import Protocol

from shapely.geometry import Polygon

from application.commands.visualize_map import VisualizationCommand
from domain.boundary.models import JapanBoundaryData
from domain.station.models import Station


class MapRenderer(Protocol):
    def render(
        self,
        stations: list[Station],
        voronoi_cells: list[Polygon],
        boundary: JapanBoundaryData,
        command: VisualizationCommand,
    ) -> None: ...
