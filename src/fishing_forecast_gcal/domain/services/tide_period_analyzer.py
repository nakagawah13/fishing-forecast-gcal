"""潮回り期間解析サービス

このモジュールは複数日分の潮回りデータから連続期間を解析し、
期間の中央日を特定するロジックを提供します。
"""

from datetime import date

from fishing_forecast_gcal.domain.models.tide import TideType


class TidePeriodAnalyzer:
    """潮回り期間解析サービス

    複数日分の潮回りデータを解析し、連続する期間の中央日を特定します。

    使用例:
        >>> tide_data = [
        ...     (date(2026, 2, 7), TideType.SPRING),
        ...     (date(2026, 2, 8), TideType.SPRING),
        ...     (date(2026, 2, 9), TideType.SPRING),
        ... ]
        >>> TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data)
        True
    """

    @staticmethod
    def is_midpoint_day(
        target_date: date,
        tide_data_list: list[tuple[date, TideType]],
    ) -> bool:
        """指定日が潮回り期間の中央日かを判定

        Args:
            target_date: 判定対象の日付
            tide_data_list: 複数日分の潮回りデータ（日付とTideTypeのタプルのリスト）

        Returns:
            True: 対象日が連続期間の中央日である
            False: 対象日が連続期間の中央日でない、またはデータに存在しない

        Note:
            - 連続期間が偶数日の場合、前半側（期間日数 // 2 の位置）を中央日とする
            - 1日のみの期間は自身が中央日となる
            - 入力リストはソートされていなくても動作する（内部でソート）
        """
        if not tide_data_list:
            return False

        # 日付でソート
        sorted_data = sorted(tide_data_list, key=lambda x: x[0])

        # 対象日が存在するか確認
        if not any(d == target_date for d, _ in sorted_data):
            return False

        # 対象日を含む連続期間を抽出
        period_start, period_end = TidePeriodAnalyzer._find_continuous_period(
            target_date, sorted_data
        )

        # 期間の中央日を計算
        midpoint = TidePeriodAnalyzer._calculate_midpoint(period_start, period_end)

        return target_date == midpoint

    @staticmethod
    def _find_continuous_period(
        target_date: date,
        sorted_data: list[tuple[date, TideType]],
    ) -> tuple[date, date]:
        """対象日を含む連続期間の開始日と終了日を取得

        Args:
            target_date: 判定対象の日付
            sorted_data: 日付でソート済みの潮回りデータ

        Returns:
            (period_start, period_end): 連続期間の開始日と終了日
        """
        # 対象日のTideTypeを取得
        target_tide_type = next(tide_type for d, tide_type in sorted_data if d == target_date)

        # 対象日のインデックスを取得
        target_index = next(i for i, (d, _) in enumerate(sorted_data) if d == target_date)

        # 後方検索（終了日を探す）
        period_end = target_date
        for i in range(target_index + 1, len(sorted_data)):
            d, tide_type = sorted_data[i]
            if tide_type != target_tide_type:
                break
            period_end = d

        # 前方検索（開始日を探す）
        period_start = target_date
        for i in range(target_index - 1, -1, -1):
            d, tide_type = sorted_data[i]
            if tide_type != target_tide_type:
                break
            period_start = d

        return period_start, period_end

    @staticmethod
    def _calculate_midpoint(period_start: date, period_end: date) -> date:
        """期間の中央日を計算

        Args:
            period_start: 期間の開始日
            period_end: 期間の終了日

        Returns:
            中央日（期間が偶数日の場合は前半側）
        """
        period_days = (period_end - period_start).days + 1  # 日数（両端含む）
        midpoint_offset = (period_days - 1) // 2  # 0-indexed で中央位置（偶数時は前半側）

        from datetime import timedelta

        return period_start + timedelta(days=midpoint_offset)
