class StationDomainError(Exception):
    """観測所ドメイン固有エラーの基底クラス。"""


class InvalidCoordinateError(StationDomainError):
    """緯度・経度が有効範囲外のときに送出されるエラー。"""


class StationDataError(StationDomainError):
    """観測所データが不正なフォーマットのときに送出されるエラー。"""
