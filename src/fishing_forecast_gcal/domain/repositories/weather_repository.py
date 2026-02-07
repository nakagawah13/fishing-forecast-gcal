"""気象予報リポジトリのインターフェース定義

このモジュールは気象予報データの取得を抽象化します。
Infrastructure層で具体的な実装（気象APIクライアント等）を提供します。
"""

from abc import ABC, abstractmethod
from datetime import date

from ..models.fishing_condition import FishingCondition
from ..models.location import Location


class IWeatherRepository(ABC):
    """気象予報リポジトリのインターフェース

    気象予報データの取得を抽象化し、Domain層とInfrastructure層を疎結合に保ちます。
    Phase 2（予報更新機能）で使用されます。

    Implementation Note:
        具体的な実装では、気象庁API、OpenWeatherMap等の気象予報APIを使用します。
        MVP では使用されませんが、Phase 2 に向けて先行定義します。
    """

    @abstractmethod
    def get_forecast(self, location: Location, target_date: date) -> FishingCondition | None:
        """指定地点・日付の気象予報を取得

        Args:
            location: 対象地点の情報（緯度・経度を含む）
            target_date: 対象日

        Returns:
            FishingCondition | None: 気象予報データ。予報が存在しない場合は None

        Raises:
            RuntimeError: データ取得に失敗した場合（API障害等）

        Note:
            - 予報の取得可能期間は実装に依存します（例: 7-14日先まで）
            - 取得できない場合（遠い未来の日付等）は None を返します
            - 風速・風向・気圧に加え、注意レベル（safe/caution/danger）を含みます
        """
        ...
