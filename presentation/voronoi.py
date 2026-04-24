import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon


def build_all_voronoi_cells(
    points: np.ndarray,
    clip_box: Polygon,
) -> list[Polygon | None]:
    vor = Voronoi(points)
    center = points.mean(axis=0)
    extend_radius = float(np.ptp(points, axis=0).max() * 5)

    all_ridges: dict[int, list[tuple[int, int, int]]] = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    new_vertices = vor.vertices.tolist()
    cells: list[Polygon | None] = []

    for p_idx in range(len(points)):
        region = vor.regions[vor.point_region[p_idx]]
        if not region:
            cells.append(None)
            continue

        if -1 not in region:
            verts = vor.vertices[region]
        else:
            new_region = [v for v in region if v >= 0]
            for q_idx, v1, v2 in all_ridges.get(p_idx, []):
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0:
                    continue
                tangent = points[q_idx] - points[p_idx]
                tangent /= np.linalg.norm(tangent)
                normal = np.array([-tangent[1], tangent[0]])
                midpoint = (points[p_idx] + points[q_idx]) / 2.0
                sign = np.sign(np.dot(midpoint - center, normal))
                far_point = vor.vertices[v2] + sign * normal * extend_radius
                new_vertices.append(far_point.tolist())
                new_region.append(len(new_vertices) - 1)

            verts_arr = np.array([new_vertices[v] for v in new_region])
            c = verts_arr.mean(axis=0)
            angles = np.arctan2(verts_arr[:, 1] - c[1], verts_arr[:, 0] - c[0])
            verts = verts_arr[np.argsort(angles)]

        try:
            poly = Polygon(verts)
            if not poly.is_valid:
                poly = poly.buffer(0)
            clipped = poly.intersection(clip_box)
            cells.append(clipped if not clipped.is_empty else None)
        except Exception:
            cells.append(None)

    return cells
