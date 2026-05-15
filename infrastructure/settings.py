import os

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_DIR: str = os.path.join(_BASE_DIR, "data")
OUTPUT_DIR: str = os.path.join(_BASE_DIR, "output")
GEOJSON_PATH: str = os.path.join(_BASE_DIR, "japan.geojson")
