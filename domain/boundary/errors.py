class BoundaryDomainError(Exception):
    """境界ドメイン固有エラーの基底クラス。"""


class BoundaryLoadError(BoundaryDomainError):
    """境界データの読み込みに失敗したときに送出されるエラー。"""


class BoundaryDownloadError(BoundaryDomainError):
    """GeoJSON のダウンロードに失敗したときに送出されるエラー。"""
