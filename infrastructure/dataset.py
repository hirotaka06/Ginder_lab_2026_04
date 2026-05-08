from pathlib import Path

from infrastructure.settings import DATA_DIR


class DatasetError(Exception):
    """データセットディレクトリの解決に失敗したときに送出されるエラー。"""


def resolve_dataset_dir(name: str) -> Path:
    """データセット名から絶対パスを返す。

    Args:
        name: data/ 直下のディレクトリ名（例: "pollen"）

    Raises:
        DatasetError: ディレクトリが存在しない場合
    """
    dataset_dir = Path(DATA_DIR) / name
    if not dataset_dir.is_dir():
        raise DatasetError(
            f"データセットが見つかりません: {dataset_dir}\n"
            f"  data/ 内に '{name}/' ディレクトリを作成してください。"
        )
    return dataset_dir


def find_csv_in(dataset_dir: Path) -> Path:
    """ディレクトリ内の CSV ファイルを1つ返す。

    Raises:
        DatasetError: CSV が存在しない、または複数ある場合
    """
    csv_files = list(dataset_dir.glob("*.csv"))
    if not csv_files:
        raise DatasetError(f"CSVファイルが見つかりません: {dataset_dir}")
    if len(csv_files) > 1:
        files = ", ".join(f.name for f in csv_files)
        raise DatasetError(
            f"CSVファイルが複数あります。どれを使うか指定してください: {files}"
        )
    return csv_files[0]


def find_config_in(dataset_dir: Path) -> Path:
    """ディレクトリ内の config.py を返す。

    Raises:
        DatasetError: config.py が存在しない場合
    """
    config_path = dataset_dir / "config.py"
    if not config_path.exists():
        raise DatasetError(f"config.py が見つかりません: {dataset_dir}")
    return config_path
