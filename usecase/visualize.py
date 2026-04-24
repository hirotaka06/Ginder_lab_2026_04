from dataclasses import dataclass

from domain.interfaces import DataLoader
from presentation.plot import plot_voronoi_japan


@dataclass
class VisualizationConfig:
    title: str
    colorbar_label: str
    output_path: str
    legend_labels: list[str] | None = None
    vmin: float | None = None
    vmax: float | None = None
    cmap_name: str = "YlOrRd"


def run_visualization(loader: DataLoader, config: VisualizationConfig) -> None:
    records = loader.load()
    stations = [{"name": r.name, "lat": r.lat, "lon": r.lon} for r in records]
    values = [r.value for r in records]

    plot_voronoi_japan(
        stations=stations,
        values=values,
        title=config.title,
        colorbar_label=config.colorbar_label,
        legend_labels=config.legend_labels,
        vmin=config.vmin,
        vmax=config.vmax,
        cmap_name=config.cmap_name,
        output_path=config.output_path,
    )
