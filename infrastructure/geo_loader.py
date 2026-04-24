import json
import os

import requests
from shapely.geometry import shape as shapely_shape
from shapely.ops import unary_union

_GEOJSON_PATH = os.path.join(os.path.dirname(__file__), "..", "japan.geojson")
_GEOJSON_URL = "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"


def load_japan_geojson() -> dict:
    if not os.path.exists(_GEOJSON_PATH):
        print(f"GeoJSON をダウンロード中: {_GEOJSON_URL}")
        resp = requests.get(_GEOJSON_URL, timeout=15)
        resp.raise_for_status()
        with open(_GEOJSON_PATH, "w", encoding="utf-8") as f:
            f.write(resp.text)
    with open(_GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_japan_boundary() -> tuple[object, list[object]]:
    """(japan_union, pref_polys) を返す。pref_polys は id 昇順。"""
    geojson = load_japan_geojson()
    features = sorted(geojson["features"], key=lambda f: f["properties"]["id"])

    pref_polys = []
    for feature in features:
        geom = shapely_shape(feature["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        pref_polys.append(geom)

    return unary_union(pref_polys), pref_polys
