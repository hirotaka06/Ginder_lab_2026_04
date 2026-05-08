# ginder

日本全国の観測データをボロノイ図として可視化するツール。
時系列データには GIF / MP4 アニメーションの生成にも対応している。

---

## セットアップ

### 1. uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.zshrc   # パスを反映
uv --version      # 確認
```

### 2. 依存パッケージのインストール

```bash
uv sync
```

### 3. ffmpeg（MP4 出力に必要）

```bash
brew install ffmpeg
```

---

## 使い方

### 基本：ボロノイ図を1枚生成

```bash
uv run python main.py <データセット名> <値の列名>
```

| 引数 | 説明 |
|------|------|
| `<データセット名>` | `data/` 内のディレクトリ名 |
| `<値の列名>` | CSV の中で色に使う列名 |

```bash
# 花粉（全国）
uv run python main.py pollen pollen_level

# 福島県の空間線量率（2011年4月）
uv run python main.py fukushima 2011_04 --prefecture 福島県
```

生成画像は `output/` に保存されます。

---

### オプション：観測点の丸印・ラベルの表示切り替え

`--no-points` と `--no-labels` で丸印・ラベルをそれぞれ非表示にできます。

| オプション | 効果 |
|-----------|------|
| （デフォルト） | 丸印・ラベル両方表示 |
| `--no-labels` | ラベルだけ非表示 |
| `--no-points` | 丸印だけ非表示 |
| `--no-points --no-labels` | 両方非表示（ボロノイ面のみ） |

```bash
# ラベルなし
uv run python main.py fukushima 2011_04 --prefecture 福島県 --no-labels

# 丸印・ラベルともに非表示
uv run python main.py fukushima 2011_04 --prefecture 福島県 --no-points --no-labels
```

動画生成スクリプトでも同じオプションが使えます。

```bash
uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県 --no-points --no-labels
```

---

### オプション：都道府県に絞り込む

`--prefecture`（`-p`）を付けると、指定した都道府県内の観測点だけで描画します。

```bash
uv run python main.py radioactivity radioactivity --prefecture 茨城県
uv run python main.py fukushima 2011_04 --prefecture 福島県
```

---

### 時系列：ボロノイ動画を生成（GIF / MP4）

時系列データ（列名が `YYYY_MM` 形式の対応幅 CSV）から動画を生成します。

```bash
uv run python scripts/generate_voronoi_video.py <データセット名> [オプション]
```

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--prefecture`, `-p` | なし | 都道府県に絞り込む |
| `--output`, `-o` | 自動命名 | 出力ファイルパス（`.gif` または `.mp4`） |
| `--fps` | `1.0` | フレームレート（フレーム/秒） |

```bash
# GIF（デフォルト）
uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県

# MP4（ffmpeg が必要）
uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県 \
  --output output/fukushima/mp4/fukushima.mp4 --fps 2
```

出力先：

```
output/<データセット名>/
├── png/            ← 各コマの PNG（YYYY_MM.png）
├── gif/            ← GIF アニメーション
└── mp4/            ← MP4 動画
```

---

## データセット

### `data/pollen/` — 花粉飛散量

全国の花粉観測データ。

```bash
uv run python main.py pollen pollen_level
```

### `data/fukushima/` — 福島県 空間線量率（2011年3月〜2012年3月）

福島県公式サイトの月次モニタリングデータ（93観測ポスト）。
時系列動画の生成に対応しています。

```bash
# 単月のボロノイ図
uv run python main.py fukushima 2011_04 --prefecture 福島県

# 時系列動画（GIF）
uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県

# 時系列動画（MP4）
uv run python scripts/generate_voronoi_video.py fukushima --prefecture 福島県 \
  --output output/fukushima/mp4/fukushima.mp4 --fps 2
```

**フォーマッター（初回のみ実行）：**

```bash
# data/fukushima/format/formatter.ipynb を Jupyter で開いて実行
# → 福島県サイトから CSV を自動ダウンロード・ジオコーディング・CSV 生成
```

---

## 独自データセットの追加方法

1. `data/<名前>/` ディレクトリを作成
2. 以下の形式で CSV を配置

   ```
   name,lat,lon,<値の列名>
   東京,35.69,139.69,3.82
   大阪,34.69,135.50,2.10
   ```

3. `data/<名前>/config.py` を作成

   ```python
   from datetime import datetime
   _today = datetime.now().strftime("%Y年%m月%d日")

   title = f"タイトル\n{_today}"
   colorbar_label = "単位"
   cmap_name = "YlOrRd"        # matplotlib のカラーマップ名
   reverse_colors = False
   thresholds = [
       (0.0, "低"),
       (5.0, "中"),
       (10.0, "高"),
   ]
   ```

4. 実行

   ```bash
   uv run python main.py <名前> <値の列名>
   ```

---

## ディレクトリ構成

```
ginder/
├── main.py                          # エントリーポイント（単枚生成）
├── scripts/
│   └── generate_voronoi_video.py    # 時系列動画生成スクリプト
├── data/
│   ├── pollen/                      # 花粉データセット
│   ├── radioactivity*/              # 放射能データセット（核種別）
│   └── fukushima/                   # 福島県時系列データセット
│       ├── fukushima.csv            # 対応幅 CSV（93ポスト × 13ヶ月）
│       ├── config.py
│       └── format/                  # 生データ・フォーマッター
├── output/
│   └── fukushima/
│       ├── png/                     # 各コマ PNG
│       ├── gif/                     # GIF アニメーション
│       └── mp4/                     # MP4 動画
├── domain/                          # ドメインモデル・インターフェース
├── application/                     # ユースケース・コマンド
├── adapters/                        # CSV・GeoJSON リポジトリ実装
├── infrastructure/                  # 設定読み込み・DI コンテナ
└── japan.geojson                    # 日本の県境データ
```
