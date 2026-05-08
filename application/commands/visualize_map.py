from dataclasses import dataclass, field


@dataclass
class VisualizationCommand:
    """ユースケースへの入力パラメータ.

    Attributes:
        legend_thresholds: 凡例に表示する閾値のリスト。legend_labels と同じ長さで対応する。
                           指定しない場合は vmin〜vmax を等分割した値を使用する。
        reverse_colors:    True のとき色順を逆転させる（高い値ほど薄い色になる）。
        prefecture:        指定した場合、その都道府県内の観測所のみを描画する。
                           例: "茨城県", "北海道"
    """

    title: str
    colorbar_label: str
    output_path: str
    legend_labels: list[str] | None = None
    legend_thresholds: list[float] | None = None
    vmin: float | None = None
    vmax: float | None = None
    cmap_name: str = "YlOrRd"
    reverse_colors: bool = False
    prefecture: str | None = None
    show_points: bool = True
    show_labels: bool = True
