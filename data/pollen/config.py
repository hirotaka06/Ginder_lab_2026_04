from datetime import datetime

_today = datetime.now().strftime("%Y年%m月%d日")

title = f"日本全国 花粉飛散量 ボロノイ図\n{_today}"
colorbar_label = "花粉飛散量レベル"
cmap_name = "YlOrRd"
reverse_colors = False

thresholds = [
    (0, "なし"),
    (1, "少ない"),
    (2, "やや多い"),
    (3, "多い"),
    (4, "非常に多い"),
]
