# ginder

日本全国の観測データをボロノイ図として可視化するツールだよ。

## セットアップ

### 1. uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストール後、ターミナルを再起動するか以下を実行してパスを反映します。

```bash
source ~/.zshrc
```

インストール確認:

```bash
uv --version
```

### 2. 依存パッケージのインストール

リポジトリのルートで実行します。

```bash
uv sync
```

## 実行方法

```bash
uv run python main.py <CSVファイルパス> [値の列名]
```

| 引数 | 必須 | 説明 |
|------|------|------|
| `<CSVファイルパス>` | ✅ | 読み込む CSV ファイルのパス |
| `[値の列名]` | ❌ | 色に使う列名（省略すると `pollen_level`） |

### 実行例

```bash
uv run python main.py pollen_mock.csv pollen_level
```

生成された画像は `output/` フォルダに保存されます。

## CSV フォーマット

ヘッダー行が必須です。

```
name,lat,lon,pollen_level
東京,35.69,139.69,3.82
大阪,34.69,135.50,2.10
...
```

## 設定

`config/settings.py` で出力先フォルダを変更できます。

```python
# デフォルト: プロジェクトルート直下の output/
OUTPUT_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))

# 任意のパスに変更する場合
# OUTPUT_DIR: str = "/Users/yourname/Desktop/voronoi_images"
```

## ディレクトリ構成

```
ginder/
├── main.py                  # エントリーポイント
├── config/
│   └── settings.py          # 出力先などの設定
├── domain/
│   ├── models.py            # エンティティ（StationRecord）
│   └── interfaces.py        # 抽象インターフェース（DataLoader）
├── usecase/
│   └── visualize.py         # ユースケース（run_visualization）
├── infrastructure/
│   ├── geo_loader.py        # GeoJSON 読み込み・境界構築
│   └── csv_loader.py        # CSV からのデータ読み込み
├── presentation/
│   ├── voronoi.py           # ボロノイセル計算
│   └── plot.py              # matplotlib による描画
└── output/                  # 生成画像の保存先（自動作成）
```
