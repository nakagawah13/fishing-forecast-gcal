"""潮汐データリポジトリのインターフェース定義

このモジュールは潮汐データの取得を抽象化します。
Infrastructure層で具体的な実装（UTideライブラリ、APIクライアント等）を提供します。
"""

from abc import ABC, abstractmethod
from datetime import date

from ..models.location import Location
from ..models.tide import Tide


class ITideDataRepository(ABC):
    """潮汐データリポジトリのインターフェース

    潮汐データの取得を抽象化し、Domain層とInfrastructure層を疎結合に保ちます。
    依存性逆転の原則（DIP）に基づき、Domain層がInfrastructure層に依存しないようにします。

    Implementation Note:
        具体的な実装では、以下のいずれかの方法で潮汐データを取得します:
        - 潮汐計算ライブラリ（UTide等）による計算
        - 潮汐予報API（気象庁等）からの取得
    """

    @abstractmethod
    def get_tide_data(self, location: Location, target_date: date) -> Tide:
        """指定地点・日付の潮汐データを取得

        Args:
            location: 対象地点の情報（緯度・経度を含む）
            target_date: 対象日

        Returns:
            Tide: 潮汐データ（満潮・干潮・潮回りを含む）

        Raises:
            ValueError: 地点または日付が不正な場合
            RuntimeError: データ取得に失敗した場合（API障害、計算エラー等）

        Note:
            - 計算精度は実装に依存します（目標: 公式潮見表に対し ±10cm以内）
            - タイムゾーンは `location` の地域に応じて設定されます
        """
        ...

    @abstractmethod
    def get_hourly_heights(
        self, location: Location, target_date: date
    ) -> list[tuple[float, float]]:
        """指定地点・日付の時系列潮位データを取得（グラフ描画用）

        タイドグラフ画像の生成に使用する時系列データを返します。
        時刻は 0.0〜24.0 の float 値（時間単位）、潮位は cm 単位です。

        Args:
            location: 対象地点の情報
            target_date: 対象日

        Returns:
            list[tuple[float, float]]: (時刻(h), 潮位(cm)) のタプルリスト

        Raises:
            ValueError: 地点または日付が不正な場合
            RuntimeError: データ取得に失敗した場合
        """
        ...
