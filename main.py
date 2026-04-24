import os
import sys
from datetime import datetime

from config.settings import OUTPUT_DIR
from infrastructure.csv_loader import CSVDataLoader
from usecase.visualize import VisualizationConfig, run_visualization


def main() -> None:
    """使い方: uv run python main.py <csvファイルパス> [値の列名]"""
    if len(sys.argv) < 2:
        print("使い方: uv run python main.py <csvファイルパス> [値の列名]")
        print("例:     uv run python main.py pollen_mock.csv pollen_level")
        sys.exit(1)

    csv_path = sys.argv[1]
    value_column = sys.argv[2] if len(sys.argv) > 2 else "pollen_level"

    if not os.path.exists(csv_path):
        print(f"エラー: CSV ファイルが見つかりません → {csv_path}")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y年%m月%d日")
    stem = os.path.splitext(os.path.basename(csv_path))[0]
    output_path = os.path.join(OUTPUT_DIR, f"{stem}_voronoi.png")

    loader = CSVDataLoader(csv_path, value_column=value_column)

    config = VisualizationConfig(
        title=f"日本全国 花粉飛散量 ボロノイ図\n{today}（ヒノキ花粉シーズン）",
        colorbar_label="花粉飛散量レベル",
        legend_labels=["なし", "少ない", "やや多い", "多い", "非常に多い"],
        vmin=0,
        vmax=4,
        cmap_name="YlOrRd",
        output_path=output_path,
    )

    run_visualization(loader, config)


if __name__ == "__main__":
    main()
