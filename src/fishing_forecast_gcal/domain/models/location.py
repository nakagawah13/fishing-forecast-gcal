"""地点情報関連のドメインモデル

このモジュールは釣行地点に関する情報を定義します。
- Location: 地点の不変ID、名称、緯度・経度
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    """釣行地点の情報

    設定ファイルで定義される釣行地点の情報を表現します。
    `id` は不変IDであり、表示名（`name`）が変更されてもイベントIDが変わらないようにします。

    Attributes:
        id: 不変ID（config.yamlの locations[].id）
        name: 表示名（例: "東京湾", "相模湾"）
        latitude: 緯度（-90 ~ 90の範囲）
        longitude: 経度（-180 ~ 180の範囲）

    Raises:
        ValueError: バリデーションエラー時

    Note:
        MVP では1地点のみサポート。複数地点対応はフェーズ3で実装予定。
    """

    id: str
    name: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        """インスタンス化後のバリデーション"""
        # idの検証
        if not self.id or not self.id.strip():
            raise ValueError("id must not be empty")

        # nameの検証
        if not self.name or not self.name.strip():
            raise ValueError("name must not be empty")

        # 緯度の範囲チェック
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"latitude must be between -90 and 90, got {self.latitude}")

        # 経度の範囲チェック
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"longitude must be between -180 and 180, got {self.longitude}")
