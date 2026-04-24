import os

# 生成した画像の保存先フォルダ（存在しない場合は自動作成される）
OUTPUT_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output"))
