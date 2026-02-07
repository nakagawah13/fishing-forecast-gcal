"""潮回りを判定するドメインサービス

このモジュールは潮位差と月齢から潮回り（大潮、中潮、小潮など）を
判定するロジックを提供します。
"""

from fishing_forecast_gcal.domain.models.tide import TideType


class TideTypeClassifier:
    """潮回りを判定するドメインサービス

    潮位差と月齢から、TideType（大潮、中潮、小潮、長潮、若潮）を判定します。

    判定基準:
    - 基本的には月齢で判定（新月・満月±3日は大潮など）
    - 潮位差が極端な場合は補正を行う

    使用例:
        >>> tide_type = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=0.0)
        >>> tide_type
        <TideType.SPRING: '大潮'>
    """

    # 潮位差による補正の閾値（cm）
    _LARGE_TIDE_RANGE_THRESHOLD = 180.0  # これ以上なら大潮方向に補正
    _SMALL_TIDE_RANGE_THRESHOLD = 80.0  # これ未満なら小潮方向に補正

    @staticmethod
    def classify(tide_range_cm: float, moon_age: float) -> TideType:
        """潮位差と月齢から潮回りを判定

        Args:
            tide_range_cm: 潮位差（満潮高さ - 干潮高さ、cm）
            moon_age: 月齢（0-29.5、0=新月、15=満月）

        Returns:
            TideType: 判定された潮回り

        Raises:
            ValueError: 入力値が不正な場合
        """
        # 入力値のバリデーション
        if tide_range_cm < 0:
            raise ValueError(f"tide_range_cm must be non-negative, got {tide_range_cm}")
        if not (0 <= moon_age <= 29.5):
            raise ValueError(f"moon_age must be between 0 and 29.5, got {moon_age}")

        # 月齢による基本判定
        base_type = TideTypeClassifier._classify_by_moon_age(moon_age)

        # 潮位差による補正
        return TideTypeClassifier._adjust_by_tide_range(base_type, tide_range_cm)

    @staticmethod
    def _classify_by_moon_age(moon_age: float) -> TideType:
        """月齢のみで潮回りを判定

        Args:
            moon_age: 月齢（0-29.5）

        Returns:
            TideType: 月齢から判定された潮回り
        """
        # 大潮: 新月±3日、満月±3日
        if (0 <= moon_age <= 3) or (12 <= moon_age <= 18) or (26.5 <= moon_age <= 29.5):
            return TideType.SPRING

        # 小潮（上弦系）: 5-8（上弦7±2の前半）
        if 5 <= moon_age < 8:
            return TideType.NEAP

        # 長潮（上弦系）: 8-9（上弦1-2日後、小潮末期）
        if 8 <= moon_age < 9:
            return TideType.LONG

        # 若潮（上弦系）: 9-10（長潮の翌日）
        if 9 <= moon_age < 10:
            return TideType.YOUNG

        # 小潮（下弦系）: 20-23（下弦22±2の前半）
        if 20 <= moon_age < 23:
            return TideType.NEAP

        # 長潮（下弦系）: 23-24（下弦1-2日後、小潮末期）
        if 23 <= moon_age < 24:
            return TideType.LONG

        # 若潮（下弦系）: 24-25（長潮の翌日）
        if 24 <= moon_age < 25:
            return TideType.YOUNG

        # 中潮: その他の期間
        return TideType.MODERATE

    @staticmethod
    def _adjust_by_tide_range(base_type: TideType, tide_range_cm: float) -> TideType:
        """潮位差による補正

        潮位差が極端に大きい・小さい場合、潮回りを補正します。

        Args:
            base_type: 月齢から判定された基本の潮回り
            tide_range_cm: 潮位差（cm）

        Returns:
            TideType: 補正後の潮回り
        """
        # 潮位差が非常に大きい場合: 中潮を大潮に昇格
        if tide_range_cm >= TideTypeClassifier._LARGE_TIDE_RANGE_THRESHOLD:
            if base_type == TideType.MODERATE:
                return TideType.SPRING

        # 潮位差が非常に小さい場合: 大潮を中潮に降格
        if tide_range_cm < TideTypeClassifier._SMALL_TIDE_RANGE_THRESHOLD:
            if base_type == TideType.SPRING:
                return TideType.MODERATE

        return base_type
