"""時系列ボロノイ動画生成スクリプト。

対応幅CSV（name, lat, lon, 2011_03, 2011_04, …）を読み込み、
各時期のボロノイ図フレームを生成して GIF または MP4 動画にまとめる。

使い方:
    uv run python scripts/generate_voronoi_video.py fukushima
    uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県
    uv run python scripts/generate_voronoi_video.py fukushima --output output/fukushima.mp4 --fps 2
"""

import argparse
import sys
import tempfile
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from application.commands.visualize_map import VisualizationCommand  # noqa: E402
from application.use_cases.visualize_map import PrefectureFilterError  # noqa: E402
from infrastructure.config_loader import ConfigLoadError, load_map_config  # noqa: E402
from infrastructure.container import build_visualize_map_use_case  # noqa: E402
from infrastructure.dataset import DatasetError, find_config_in, resolve_dataset_dir  # noqa: E402
from infrastructure.settings import DATA_DIR, OUTPUT_DIR  # noqa: E402


plt.rcParams["font.family"] = ["Hiragino Sans", "AppleGothic", "sans-serif"]


# ── ヘルパー ───────────────────────────────────────────────────────────────

def detect_period_columns(df: pd.DataFrame) -> list[str]:
    """DataFrame から時系列を表す列名を抽出する。

    対応形式:
      - 月単位:  YYYY_MM           (例: 2011_04)
      - 日単位:  YYYY_MM_DD        (例: 2011_04_24)
      - 時単位:  YYYY_MM_DD_HH     (例: 2011_04_24_12)
      - 分単位:  YYYY_MM_DD_HH_MM  (例: 2011_04_24_12_16)
    """
    import re
    pattern = re.compile(r"^\d{4}(?:_\d{2}){1,4}$")
    return [col for col in df.columns if pattern.match(col)]


def period_to_label(period: str) -> str:
    """期間カラム名を日本語ラベルに変換する。

    例:
      '2011_04'             → '2011年4月'
      '2011_04_24'          → '2011年4月24日'
      '2011_04_24_12'       → '2011年4月24日 12時'
      '2011_04_24_12_16'    → '2011年4月24日 12:16'
    """
    parts = period.split("_")
    year = parts[0]
    if len(parts) == 2:
        return f"{year}年{int(parts[1]):d}月"
    if len(parts) == 3:
        return f"{year}年{int(parts[1]):d}月{int(parts[2]):d}日"
    if len(parts) == 4:
        return f"{year}年{int(parts[1]):d}月{int(parts[2]):d}日 {int(parts[3]):d}時"
    if len(parts) == 5:
        return (
            f"{year}年{int(parts[1]):d}月{int(parts[2]):d}日 "
            f"{int(parts[3]):02d}:{int(parts[4]):02d}"
        )
    return period


def save_single_frame(
    csv_path: str,
    period_col: str,
    frame_path: str,
    config,
    prefecture: str | None,
    vmin: float,
    vmax: float,
    title_base: str,
    show_points: bool = True,
    show_labels: bool = True,
) -> bool:
    """単一時期の PNG フレームを生成して保存する。"""
    period_label = period_to_label(period_col)
    title = f"{title_base}\n{period_label}"
    if prefecture:
        title += f"【{prefecture}】"

    legend_thresholds = [t.value for t in config.thresholds] or None
    legend_labels = [t.label for t in config.thresholds] or None

    use_case = build_visualize_map_use_case(csv_path, period_col)
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
        output_path=frame_path,
        prefecture=prefecture,
        show_points=show_points,
        show_labels=show_labels,
        show_cell_borders=config.show_cell_borders,
    )
    try:
        use_case.execute(command)
        return True
    except PrefectureFilterError as exc:
        print(f"    ⚠ {exc}")
        return False


def make_period_csv(df: pd.DataFrame, period_col: str, dest: Path) -> int:
    """対応幅CSVから単期間の CSV（name, lat, lon, <period>）を生成する。"""
    sub = df[["name", "lat", "lon", period_col]].dropna(subset=[period_col])
    sub = sub.rename(columns={period_col: period_col})  # 列名は変えない
    sub.to_csv(dest, index=False, encoding="utf-8")
    return len(sub)


# ── 動画合成 ───────────────────────────────────────────────────────────────

def combine_frames_to_gif(frame_paths: list[Path], output_path: Path, fps: float) -> None:
    """PIL (Pillow) を使って PNG フレームを GIF アニメーションに合成する。"""
    from PIL import Image

    duration_ms = int(1000 / fps)
    frames = [Image.open(p).convert("RGBA") for p in frame_paths]
    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )


def combine_frames_to_mp4(frame_paths: list[Path], output_path: Path, fps: float) -> None:
    """ffmpeg を使って PNG フレームを MP4 動画に合成する。"""
    import subprocess
    import shutil

    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg が見つかりません。brew install ffmpeg でインストールしてください。")

    # ffmpeg はファイル名パターンを受け取るので連番リネームが必要
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for i, src in enumerate(frame_paths):
            (tmp_path / f"frame_{i:04d}.png").symlink_to(src.resolve())

        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(tmp_path / "frame_%04d.png"),
            # H.264 は縦横が 2 の倍数でないといけないため、奇数サイズを自動切り捨て
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_path.resolve()),
        ]
        subprocess.run(cmd, check=True, capture_output=True)


# ── メイン ────────────────────────────────────────────────────────────────

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="対応幅CSVから時系列ボロノイ動画を生成します。",
        epilog=(
            "例:\n"
            "  uv run python scripts/generate_voronoi_video.py fukushima\n"
            "  uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県 --fps 2"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("dataset", help="データセット名（data/ 内のディレクトリ名）")
    parser.add_argument(
        "--prefecture", "-p",
        metavar="都道府県名",
        default=None,
        help="指定した都道府県に絞り込む（例: 福島県）",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="ファイルパス",
        default=None,
        help="出力ファイルパス（.gif または .mp4、省略時は output/ に自動命名）",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=1.0,
        help="フレームレート（秒あたりフレーム数、デフォルト: 1）",
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


def main() -> None:
    args = _build_arg_parser().parse_args()

    # ── データセット解決 ─────────────────────────────────────
    try:
        dataset_dir = resolve_dataset_dir(args.dataset)
        config_path = find_config_in(dataset_dir)
    except DatasetError as exc:
        print(f"エラー: {exc}")
        sys.exit(1)

    # CSVは幅広形式（name, lat, lon, 2011_03, ...）
    csv_candidates = list(dataset_dir.glob("*.csv"))
    if not csv_candidates:
        print(f"エラー: CSVファイルが見つかりません: {dataset_dir}")
        sys.exit(1)
    wide_csv = csv_candidates[0]

    try:
        config = load_map_config(str(config_path))
    except ConfigLoadError as exc:
        print(f"エラー: {exc}")
        sys.exit(1)

    df = pd.read_csv(wide_csv, encoding="utf-8")
    period_cols = detect_period_columns(df)
    if not period_cols:
        print("エラー: YYYY_MM 形式の期間列が見つかりません。")
        sys.exit(1)

    print(f"データセット: {args.dataset}")
    print(f"期間: {period_cols[0]} 〜 {period_cols[-1]}（{len(period_cols)} フレーム）")
    print(f"都道府県フィルタ: {args.prefecture or 'なし（全国）'}")

    # vmin / vmax を全期間で統一（色スケールを固定することで変化が分かりやすくなる）
    numeric_cols = df[period_cols].select_dtypes(include="number")
    vmin = float(numeric_cols.min().min())
    vmax = float(numeric_cols.max().max())
    if config.thresholds:
        vmin = config.thresholds[0].value
        vmax = config.thresholds[-1].value
    print(f"カラースケール: {vmin} 〜 {vmax} {config.colorbar_label}")

    # タイトルのベース部分（期間ラベルを除いた部分）
    title_lines = config.title.split("\n") if config.title else [args.dataset]
    title_base = "\n".join(title_lines[:2])  # 最初の2行をベースとして使用

    # ── 出力ディレクトリ決定 ──────────────────────────────────
    # output/{dataset}/png/  … 各コマの PNG
    # output/{dataset}/gif/  … アニメーション GIF（または mp4/）
    base_out = Path(OUTPUT_DIR) / args.dataset
    png_dir = base_out / "png"
    gif_dir = base_out / "gif"
    png_dir.mkdir(parents=True, exist_ok=True)
    gif_dir.mkdir(parents=True, exist_ok=True)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        pref_part = f"_{args.prefecture}" if args.prefecture else ""
        output_path = gif_dir / f"{args.dataset}{pref_part}_voronoi.gif"

    use_mp4 = output_path.suffix.lower() == ".mp4"

    # ── フレーム生成 ─────────────────────────────────────────
    with tempfile.TemporaryDirectory() as tmp_root:
        period_csv_dir = Path(tmp_root) / "period_csvs"
        period_csv_dir.mkdir()

        frame_paths: list[Path] = []

        for i, period in enumerate(period_cols):
            print(f"\n[{i+1}/{len(period_cols)}] {period_to_label(period)}...")

            # 単期間CSVを一時ファイルに書き出す
            period_csv = period_csv_dir / f"{period}.csv"
            n_stations = make_period_csv(df, period, period_csv)
            print(f"  観測点数: {n_stations}")

            # PNG は output/{dataset}/png/{period}.png として永続保存
            frame_path = png_dir / f"{period}.png"
            success = save_single_frame(
                csv_path=str(period_csv),
                period_col=period,
                frame_path=str(frame_path),
                config=config,
                prefecture=args.prefecture,
                vmin=vmin,
                vmax=vmax,
                title_base=title_base,
                show_points=not args.no_points,
                show_labels=not args.no_labels,
            )
            if success:
                frame_paths.append(frame_path)
                print(f"  → {frame_path}")
            plt.close("all")

        if not frame_paths:
            print("\nエラー: 有効なフレームが1枚も生成されませんでした。")
            sys.exit(1)

        print(f"\n{len(frame_paths)} フレーム生成完了。動画を合成中...")

        # ── 動画合成 ─────────────────────────────────────────
        if use_mp4:
            try:
                combine_frames_to_mp4(frame_paths, output_path, args.fps)
            except Exception as exc:
                print(f"MP4 合成失敗: {exc}\nGIF に切り替えます...")
                output_path = gif_dir / output_path.with_suffix(".gif").name
                combine_frames_to_gif(frame_paths, output_path, args.fps)
        else:
            combine_frames_to_gif(frame_paths, output_path, args.fps)

        print(f"\n✓ PNG フレーム: {png_dir}/")
        print(f"✓ 動画: {output_path.resolve()}")
        print(f"  フレーム数: {len(frame_paths)}, FPS: {args.fps}")


if __name__ == "__main__":
    main()
