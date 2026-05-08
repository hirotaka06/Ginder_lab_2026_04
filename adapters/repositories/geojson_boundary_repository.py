import json
import os

import requests
from shapely.geometry import shape as shapely_shape
from shapely.ops import unary_union

from domain.boundary.errors import BoundaryDownloadError, BoundaryLoadError
from domain.boundary.models import JapanBoundaryData

_DEFAULT_GEOJSON_URL = (
    "https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson"
)


class GeoJSONBoundaryRepository:
    def __init__(
        self,
        geojson_path: str,
        url: str = _DEFAULT_GEOJSON_URL,
    ) -> None:
        self._geojson_path = geojson_path
        self._url = url

    def fetch_japan_boundary(self) -> JapanBoundaryData:
        geojson = self._load_geojson()
        prefectures, prefecture_names = self._build_prefecture_geometries(
            geojson)
        outline = unary_union(prefectures)
        return JapanBoundaryData(
            outline=outline,
            prefectures=prefectures,
            prefecture_names=prefecture_names,
        )

    def _load_geojson(self) -> dict:
        if not os.path.exists(self._geojson_path):
            self._download_geojson()
        try:
            with open(self._geojson_path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise BoundaryLoadError from exc

    def _download_geojson(self) -> None:
        print(f"GeoJSON をダウンロード中: {self._url}")
        try:
            resp = requests.get(self._url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise BoundaryDownloadError from exc
        with open(self._geojson_path, "w", encoding="utf-8") as f:
            f.write(resp.text)

    def _build_prefecture_geometries(
        self, geojson: dict
    ) -> tuple[list[object], list[str]]:
        """都道府県ごとのポリゴンと日本語名を返す。"""
        features = sorted(
            geojson["features"],
            key=lambda f: f["properties"]["id"],
        )
        geoms = []
        names = []
        for feat in features:
            geom = shapely_shape(feat["geometry"])
            geoms.append(geom if geom.is_valid else geom.buffer(0))
            names.append(feat["properties"].get("nam_ja", ""))
        return geoms, names
