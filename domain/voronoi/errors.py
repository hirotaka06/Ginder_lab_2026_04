class VoronoiDomainError(Exception):
    """ボロノイドメイン固有エラーの基底クラス。"""


class VoronoiComputationError(VoronoiDomainError):
    """ボロノイ図の計算に失敗したときに送出されるエラー。"""
