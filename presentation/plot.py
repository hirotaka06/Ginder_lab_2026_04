import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from shapely.geometry import MultiPolygon, Polygon

from infrastructure.geo_loader import build_japan_boundary
from presentation.voronoi import build_all_voronoi_cells

plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic", "sans-serif"]


def shapely_to_mpl_patch(geom: object, **kwargs) -> PathPatch:
    def ring_codes(ring) -> list[int]:
        codes = [MplPath.LINETO] * len(ring.coords)
        codes[0] = MplPath.MOVETO
        codes[-1] = MplPath.CLOSEPOLY
        return codes

    def poly_to_verts_codes(polygon: Polygon):
        verts = list(polygon.exterior.coords)
        codes = ring_codes(polygon.exterior)
        for interior in polygon.interiors:
            verts += list(interior.coords)
            codes += ring_codes(interior)
        return verts, codes

    all_verts, all_codes = [], []
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    for p in polys:
        v, c = poly_to_verts_codes(p)
        all_verts.extend(v)
        all_codes.extend(c)

    return PathPatch(MplPath(all_verts, all_codes), **kwargs)


def plot_voronoi_japan(
    stations: list[dict],
    values: list[float],
    *,
    title: str = "日本全国 ボロノイ図",
    colorbar_label: str = "値",
    legend_labels: list[str] | None = None,
    vmin: float | None = None,
    vmax: float | None = None,
    cmap_name: str = "YlOrRd",
    output_path: str = "voronoi_japan.png",
) -> None:
    values_arr = np.asarray(values, dtype=float)
    _vmin = vmin if vmin is not None else float(values_arr.min())
    _vmax = vmax if vmax is not None else float(values_arr.max())

    print("日本の境界データを構築中...")
    japan_boundary, pref_polys = build_japan_boundary()

    points = np.array([[st["lon"], st["lat"]] for st in stations])

    print("ボロノイ図を計算中...")
    bounds = japan_boundary.bounds
    margin = 15.0
    clip_box = Polygon(
        [
            (bounds[0] - margin, bounds[1] - margin),
            (bounds[2] + margin, bounds[1] - margin),
            (bounds[2] + margin, bounds[3] + margin),
            (bounds[0] - margin, bounds[3] + margin),
        ]
    )
    voronoi_cells = build_all_voronoi_cells(points, clip_box)

    cmap = plt.colormaps[cmap_name]
    norm = mcolors.Normalize(vmin=_vmin, vmax=_vmax)

    fig, ax = plt.subplots(figsize=(11, 14))
    ax.set_aspect("equal")

    # ボロノイの微小隙間を隠すため、先に陸地を薄いグレーで塗る
    ax.add_patch(
        shapely_to_mpl_patch(
            japan_boundary,
            facecolor="#dddddd",
            edgecolor="none",
            zorder=1,
        )
    )

    for i, cell_poly in enumerate(voronoi_cells):
        if cell_poly is None or cell_poly.is_empty:
            continue
        clipped = cell_poly.intersection(japan_boundary)
        if clipped.is_empty:
            continue
        ax.add_patch(
            shapely_to_mpl_patch(
                clipped,
                facecolor=cmap(norm(values[i])),
                edgecolor="white",
                linewidth=0.4,
                alpha=0.88,
                zorder=2,
            )
        )

    for pref_geom in pref_polys:
        polys = (
            list(pref_geom.geoms) if isinstance(pref_geom, MultiPolygon) else [pref_geom]
        )
        for p in polys:
            x, y = p.exterior.xy
            ax.plot(x, y, color="#555555", linewidth=0.45, alpha=0.8, zorder=3)

    ax.scatter(
        points[:, 0],
        points[:, 1],
        c=values,
        cmap=cmap,
        norm=norm,
        s=28,
        zorder=5,
        edgecolors="black",
        linewidths=0.6,
    )

    for st in stations:
        ax.annotate(
            st["name"],
            xy=(st["lon"], st["lat"]),
            xytext=(3, 2),
            textcoords="offset points",
            fontsize=5.8,
            zorder=6,
            color="#111111",
        )

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="vertical", fraction=0.025, pad=0.02)
    cbar.set_label(colorbar_label, fontsize=11)

    if legend_labels:
        tick_vals = np.linspace(_vmin, _vmax, len(legend_labels))
        legend_patches = [
            plt.Rectangle((0, 0), 1, 1, fc=cmap(norm(v)), ec="gray", lw=0.5)
            for v in tick_vals
        ]
        ax.legend(
            legend_patches,
            legend_labels,
            title=colorbar_label,
            loc="lower left",
            fontsize=8,
            title_fontsize=9,
            framealpha=0.85,
        )

    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel("経度 (°E)", fontsize=9)
    ax.set_ylabel("緯度 (°N)", fontsize=9)

    view_bounds = japan_boundary.bounds
    view_margin = 0.8
    ax.set_xlim(view_bounds[0] - view_margin, view_bounds[2] + view_margin)
    ax.set_ylim(view_bounds[1] - view_margin, view_bounds[3] + view_margin)
    ax.grid(True, linestyle="--", alpha=0.25, linewidth=0.5, zorder=0)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✓ 保存完了: {output_path}")
    plt.close(fig)
