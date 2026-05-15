import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType


@dataclass(frozen=True)
class ThresholdEntry:
    """閾値と凡例ラベルのペア。"""

    value: float
    label: str


@dataclass(frozen=True)
class MapConfig:
    """config.py から読み込んだ描画設定。

    Attributes:
        title:              グラフタイトル。省略時は main.py 側で日付を付与する。
        colorbar_label:     カラーバーのラベル。
        cmap_name:          matplotlibカラーマップ名（カスタム名 'safecast' も可）。
        reverse_colors:     True のとき色順を逆転（高い値ほど薄い色）。
        norm_type:          色の正規化方式。'linear' または 'log'。
                            'log' のとき、最小閾値 (thresholds[0].value) は 0 より大きい必要がある。
        show_cell_borders:  True のときボロノイセルの間に白い境界線を描く（デフォルト）。
                            False にするとセル同士が地続きの面塗りになる。
        thresholds:         閾値と凡例ラベルのリスト（値の昇順で記述する）。
    """

    title: str | None = None
    colorbar_label: str = "計測値"
    cmap_name: str = "YlOrRd"
    reverse_colors: bool = False
    norm_type: str = "linear"
    show_cell_borders: bool = True
    thresholds: list[ThresholdEntry] = field(default_factory=list)


class ConfigLoadError(Exception):
    """設定ファイルの読み込み・解析に失敗したときに送出されるエラー。"""


def load_map_config(config_path: str) -> MapConfig:
    """config.py を読み込み MapConfig を返す。

    Args:
        config_path: 設定 Python ファイルのパス

    Raises:
        ConfigLoadError: ファイルが読めない / 変数の型が不正
    """
    module = _load_module(config_path)
    thresholds = _parse_thresholds(module, config_path)

    return MapConfig(
        title=_get_optional_str(module, "title"),
        colorbar_label=_get_str(module, "colorbar_label", default="計測値"),
        cmap_name=_get_str(module, "cmap_name", default="YlOrRd"),
        reverse_colors=bool(getattr(module, "reverse_colors", False)),
        norm_type=_get_norm_type(module),
        show_cell_borders=bool(getattr(module, "show_cell_borders", True)),
        thresholds=thresholds,
    )


def _load_module(config_path: str) -> ModuleType:
    path = Path(config_path)
    spec = importlib.util.spec_from_file_location("_map_config", path)
    if spec is None or spec.loader is None:
        raise ConfigLoadError(f"設定ファイルを読み込めません: {config_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:
        raise ConfigLoadError(f"設定ファイルの実行中にエラーが発生しました: {exc}") from exc
    return module


def _get_str(module: ModuleType, name: str, *, default: str) -> str:
    value = getattr(module, name, default)
    if not isinstance(value, str):
        raise ConfigLoadError(f"{name} は文字列で指定してください。")
    return value


def _get_optional_str(module: ModuleType, name: str) -> str | None:
    value = getattr(module, name, None)
    if value is not None and not isinstance(value, str):
        raise ConfigLoadError(f"{name} は文字列で指定してください。")
    return value


_VALID_NORM_TYPES = ("linear", "log")


def _get_norm_type(module: ModuleType) -> str:
    """norm_type を読み取り、'linear' または 'log' に正規化する。"""
    value = getattr(module, "norm_type", "linear")
    if not isinstance(value, str):
        raise ConfigLoadError("norm_type は文字列で指定してください。")
    if value not in _VALID_NORM_TYPES:
        raise ConfigLoadError(
            f"norm_type は {_VALID_NORM_TYPES} のいずれかを指定してください: {value!r}"
        )
    return value


def _parse_thresholds(module: ModuleType, config_path: str) -> list[ThresholdEntry]:
    raw = getattr(module, "thresholds", [])
    if not isinstance(raw, list):
        raise ConfigLoadError("thresholds はリストで指定してください。")
    entries = []
    for i, item in enumerate(raw):
        if not (isinstance(item, (list, tuple)) and len(item) == 2):
            raise ConfigLoadError(
                f"thresholds[{i}] は (値, ラベル) のタプルで指定してください。"
            )
        try:
            entries.append(ThresholdEntry(value=float(item[0]), label=str(item[1])))
        except (TypeError, ValueError) as exc:
            raise ConfigLoadError(
                f"thresholds[{i}] の値が不正です: {item}"
            ) from exc
    return entries
