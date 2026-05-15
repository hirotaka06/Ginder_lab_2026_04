import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from application.commands.visualize_map import VisualizationCommand
from domain.boundary.models import JapanBoundaryData
from domain.station.models import Station

plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic", "sans-serif"]

_VIEW_MARGIN = 0.8

# ── Safecast 公式タイルマップ風カラーマップ ───────────────────────
# 低い値（背景レベル）から高い値まで:
#   濃青 → 青 → 水色 → 緑 → 黄 → 橙 → ピンク → マゼンタ → 赤 → 暗赤
# Safecast の log スケール（0.03〜65.54 µSv/h）と組み合わせて使う想定。
_SAFECAST_COLOR_STOPS = [
    "#1d3a8c",  # dark blue (lowest, ~0.03 µSv/h 付近)
    "#2060df",  # medium blue
    "#22a0dd",  # light blue
    "#22dadd",  # cyan
    "#48e040",  # green
    "#fff020",  # yellow
    "#ffa040",  # orange
    "#ff60a0",  # pink
    "#e020c0",  # magenta
    "#c00040",  # red
    "#600020",  # dark red (highest, ~65 µSv/h 付近)
]


def _register_safecast_colormap() -> None:
    """カスタムカラーマップ 'safecast' を matplotlib に登録する（冪等）。"""
    if "safecast" in plt.colormaps():
        return
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "safecast", _SAFECAST_COLOR_STOPS, N=256,
    )
    cmap_r = cmap.reversed(name="safecast_r")
    plt.colormaps.register(cmap, name="safecast")
    plt.colormaps.register(cmap_r, name="safecast_r")


_register_safecast_colormap()


def _build_norm(
    norm_type: str, vmin: float, vmax: float,
) -> mcolors.Normalize:
    """norm_type に応じた matplotlib の Normalize インスタンスを返す。

    - 'linear' : 通常の線形スケール
    - 'log'    : 対数スケール（vmin > 0 が必要、観測値も 0 以下は clip される）
    """
    if norm_type == "log":
        if vmin <= 0:
            raise ValueError(
                f"norm_type='log' のとき vmin は 0 より大きい必要があります: vmin={vmin}"
            )
        return mcolors.LogNorm(vmin=vmin, vmax=vmax, clip=True)
    return mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)


class MapPlotter:
    def render(
        self,
        stations: list[Station],
        voronoi_cells: list[Polygon],
        boundary: JapanBoundaryData,
        command: VisualizationCommand,
    ) -> None:
        values = [st.measurement_value for st in stations]
        vmin = command.vmin if command.vmin is not None else min(values)
        vmax = command.vmax if command.vmax is not None else max(values)

        cmap_name = f"{command.cmap_name}_r" if command.reverse_colors else command.cmap_name
        cmap = plt.colormaps[cmap_name]
        norm = _build_norm(command.norm_type, vmin, vmax)

        fig, ax = plt.subplots(figsize=(11, 14))
        ax.set_aspect("equal")

        self._draw_voronoi_cells(
            ax, voronoi_cells, values, cmap, norm, boundary.outline,
            show_borders=command.show_cell_borders,
        )
        self._draw_prefecture_boundaries(ax, boundary.prefectures)
        if command.show_points:
            self._draw_station_points(ax, stations, values, cmap, norm)
        if command.show_labels:
            self._draw_station_labels(ax, stations)

        if command.legend_labels:
            self._draw_legend(
                ax, cmap, norm, vmin, vmax,
                command.legend_labels,
                command.legend_thresholds,
                command.colorbar_label,
            )

        self._configure_axes(ax, boundary.bounds, command.title)

        plt.tight_layout()
        plt.savefig(command.output_path, dpi=150, bbox_inches="tight")
        print(f"✓ 保存完了: {command.output_path}")
        plt.close(fig)

    # --- 描画サブメソッド ---

    def _draw_voronoi_cells(
        self, ax, cells, values, cmap, norm, outline, *, show_borders: bool = True,
    ) -> None:
        # show_borders=False の場合は塗りつぶしのみ（セル間の白い縁取りなし）
        edge_color = "white" if show_borders else "none"
        line_width = 0.4 if show_borders else 0.0
        for cell, value in zip(cells, values):
            if cell.is_empty:
                continue
            clipped = cell.intersection(outline)
            if clipped.is_empty:
                continue
            for poly in self._iter_polygons(clipped):
                x, y = poly.exterior.xy
                ax.fill(x, y, fc=cmap(norm(value)), ec=edge_color,
                        linewidth=line_width, alpha=0.88, zorder=2)

    def _draw_prefecture_boundaries(self, ax, prefectures) -> None:
        for pref_geom in prefectures:
            for poly in self._iter_polygons(pref_geom):
                x, y = poly.exterior.xy
                ax.plot(x, y, color="#555555",
                        linewidth=0.45, alpha=0.8, zorder=3)

    def _draw_station_points(self, ax, stations, values, cmap, norm) -> None:
        points = np.array([[st.lon, st.lat] for st in stations])
        ax.scatter(
            points[:, 0], points[:, 1],
            c=values, cmap=cmap, norm=norm,
            s=28, zorder=5, edgecolors="black", linewidths=0.6,
        )

    def _draw_station_labels(self, ax, stations) -> None:
        for st in stations:
            if st.name is None:
                continue
            ax.annotate(
                st.name, xy=(st.lon, st.lat), xytext=(3, 2),
                textcoords="offset points", fontsize=5.8, zorder=6, color="#111111",
            )

    def _draw_legend(self, ax, cmap, norm, vmin, vmax, labels, thresholds, colorbar_label) -> None:
        legend_values = thresholds if thresholds is not None else np.linspace(
            vmin, vmax, len(labels))
        legend_patches = [
            plt.Rectangle((0, 0), 1, 1, fc=cmap(norm(v)), ec="gray", lw=0.5)
            for v in legend_values
        ]
        ax.legend(
            legend_patches, labels,
            title=colorbar_label, loc="lower left",
            fontsize=8, title_fontsize=9, framealpha=0.85,
        )

    def _configure_axes(self, ax, bounds, title: str) -> None:
        minx, miny, maxx, maxy = bounds
        ax.set_xlim(minx - _VIEW_MARGIN, maxx + _VIEW_MARGIN)
        ax.set_ylim(miny - _VIEW_MARGIN, maxy + _VIEW_MARGIN)
        ax.grid(True, linestyle="--", alpha=0.25, linewidth=0.5, zorder=0)
        ax.set_title(title, fontsize=14, pad=12)
        ax.set_xlabel("経度 (°E)", fontsize=9)
        ax.set_ylabel("緯度 (°N)", fontsize=9)

    @staticmethod
    def _iter_polygons(geom: BaseGeometry) -> list[Polygon]:
        """ジオメトリから Polygon だけを取り出す。

        shapely の intersection は以下を返す可能性がある:
          - Polygon              : そのまま
          - MultiPolygon         : 構成ポリゴンを展開
          - GeometryCollection   : ポリゴン以外（点・線）が混じることがあるので Polygon のみ抽出
          - Point / LineString   : 描画対象外なのでスキップ
        """
        if geom.is_empty:
            return []
        if isinstance(geom, Polygon):
            return [geom]
        if isinstance(geom, MultiPolygon):
            return list(geom.geoms)
        if isinstance(geom, GeometryCollection):
            return [g for g in geom.geoms if isinstance(g, Polygon)]
        # Point / LineString など面を持たないジオメトリは描画できないので無視
        return []
