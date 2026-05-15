import argparse
import os
import sys
from datetime import datetime

from application.commands.visualize_map import VisualizationCommand
from application.use_cases.visualize_map import PrefectureFilterError
from infrastructure.config_loader import ConfigLoadError, load_map_config
from infrastructure.container import build_visualize_map_use_case
from infrastructure.dataset import DatasetError, find_config_in, find_csv_in, resolve_dataset_dir
from infrastructure.settings import OUTPUT_DIR


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="観測所CSVからボロノイマップを生成します。",
        epilog=(
            "例:\n"
            "  uv run python main.py pollen pollen_level\n"
            "  uv run python main.py radioactivity radioactivity --prefecture 茨城県"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("dataset", help="データセット名 (data/ 内のディレクトリ名)")
    parser.add_argument("value_column", help="計測値として使う列名")
    parser.add_argument(
        "--prefecture", "-p",
        metavar="都道府県名",
        default=None,
        help="指定した都道府県内の観測所のみに絞り込む（例: 茨城県）",
    )
    parser.add_argument(
        "--no-points",
        action="store_true",
        default=False,
        help="観測点の丸印を非表示にする",
    )
    parser.add_argument(
        "--no-labels",
        action="store_true",
        default=False,
        help="観測点名のラベルを非表示にする",
    )
    return parser


def _build_output_filename(dataset: str, prefecture: str | None) -> str:
    """出力ファイル名を組み立てる。都道府県指定時はサフィックスを付与する。"""
    if prefecture:
        return f"{dataset}_{prefecture}_voronoi.png"
    return f"{dataset}_voronoi.png"


def _append_prefecture_to_title(title: str, prefecture: str) -> str:
    """タイトルの末尾に都道府県名を追記する。"""
    return f"{title}【{prefecture}】"


def main() -> None:
    args = _build_arg_parser().parse_args()

    try:
        dataset_dir = resolve_dataset_dir(args.dataset)
        csv_path = find_csv_in(dataset_dir)
        config_path = find_config_in(dataset_dir)
    except DatasetError as exc:
        print(f"エラー: {exc}")
        sys.exit(1)

    try:
        config = load_map_config(str(config_path))
    except ConfigLoadError as exc:
        print(f"エラー: {exc}")
        sys.exit(1)

    today = datetime.now().strftime("%Y年%m月%d日")
    title = config.title if config.title else f"ボロノイ図 ({today})"

    if args.prefecture:
        title = _append_prefecture_to_title(title, args.prefecture)

    legend_thresholds = [t.value for t in config.thresholds] or None
    legend_labels = [t.label for t in config.thresholds] or None
    vmin = legend_thresholds[0] if legend_thresholds else None
    vmax = legend_thresholds[-1] if legend_thresholds else None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = _build_output_filename(args.dataset, args.prefecture)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    use_case = build_visualize_map_use_case(str(csv_path), args.value_column)

    command = VisualizationCommand(
        title=title,
        colorbar_label=config.colorbar_label,
        legend_labels=legend_labels,
        legend_thresholds=legend_thresholds,
        vmin=vmin,
        vmax=vmax,
        cmap_name=config.cmap_name,
        reverse_colors=config.reverse_colors,
        norm_type=config.norm_type,
        output_path=output_path,
        prefecture=args.prefecture,
        show_points=not args.no_points,
        show_labels=not args.no_labels,
        show_cell_borders=config.show_cell_borders,
    )

    try:
        use_case.execute(command)
    except PrefectureFilterError as exc:
        print(f"エラー: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
