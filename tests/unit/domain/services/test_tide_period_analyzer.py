"""潮回り期間解析サービスのテスト"""

from datetime import date

import pytest

from fishing_forecast_gcal.domain.models.tide import TideType
from fishing_forecast_gcal.domain.services.tide_period_analyzer import TidePeriodAnalyzer


class TestTidePeriodAnalyzer:
    """TidePeriodAnalyzer のテスト"""

    def test_single_period_3days_midpoint_is_day2(self) -> None:
        """3日間連続の場合、2日目が中央日"""
        tide_data = [
            (date(2026, 2, 7), TideType.SPRING),
            (date(2026, 2, 8), TideType.SPRING),
            (date(2026, 2, 9), TideType.SPRING),
        ]
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 7), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 9), tide_data) is False

    def test_single_period_4days_midpoint_is_day2(self) -> None:
        """4日間連続の場合、2日目が中央日（前半側）"""
        tide_data = [
            (date(2026, 2, 7), TideType.SPRING),
            (date(2026, 2, 8), TideType.SPRING),
            (date(2026, 2, 9), TideType.SPRING),
            (date(2026, 2, 10), TideType.SPRING),
        ]
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 7), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 9), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 10), tide_data) is False

    def test_single_period_5days_midpoint_is_day3(self) -> None:
        """5日間連続の場合、3日目が中央日"""
        tide_data = [
            (date(2026, 2, 7), TideType.NEAP),
            (date(2026, 2, 8), TideType.NEAP),
            (date(2026, 2, 9), TideType.NEAP),
            (date(2026, 2, 10), TideType.NEAP),
            (date(2026, 2, 11), TideType.NEAP),
        ]
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 7), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 9), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 10), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 11), tide_data) is False

    def test_multiple_periods_each_has_midpoint(self) -> None:
        """複数期間がある場合、各期間の中央日が正しく判定される"""
        tide_data = [
            (date(2026, 2, 1), TideType.SPRING),
            (date(2026, 2, 2), TideType.SPRING),
            (date(2026, 2, 3), TideType.SPRING),
            (date(2026, 2, 4), TideType.MODERATE),
            (date(2026, 2, 5), TideType.MODERATE),
            (date(2026, 2, 6), TideType.NEAP),
            (date(2026, 2, 7), TideType.NEAP),
            (date(2026, 2, 8), TideType.NEAP),
        ]
        # 大潮期間（2/1-2/3）の中央日は2/2
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 1), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 2), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 3), tide_data) is False
        # 中潮期間（2/4-2/5）の中央日は2/4（前半側）
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 4), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 5), tide_data) is False
        # 小潮期間（2/6-2/8）の中央日は2/7
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 6), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 7), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is False

    def test_single_day_period_is_midpoint(self) -> None:
        """1日のみの期間は自身が中央日"""
        tide_data = [
            (date(2026, 2, 1), TideType.SPRING),
            (date(2026, 2, 2), TideType.MODERATE),
            (date(2026, 2, 3), TideType.SPRING),
        ]
        # 2/2は単独期間なので中央日
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 2), tide_data) is True

    def test_target_date_not_in_list_returns_false(self) -> None:
        """対象日がリストに存在しない場合はFalse"""
        tide_data = [
            (date(2026, 2, 7), TideType.SPRING),
            (date(2026, 2, 8), TideType.SPRING),
            (date(2026, 2, 9), TideType.SPRING),
        ]
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 6), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 10), tide_data) is False

    def test_empty_list_returns_false(self) -> None:
        """空のリストを渡した場合はFalse"""
        tide_data: list[tuple[date, TideType]] = []
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is False

    def test_two_day_period_first_is_midpoint(self) -> None:
        """2日間連続の場合、1日目が中央日（前半側）"""
        tide_data = [
            (date(2026, 2, 7), TideType.LONG),
            (date(2026, 2, 8), TideType.LONG),
        ]
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 7), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is False

    def test_unsorted_list_works_correctly(self) -> None:
        """ソートされていないリストでも正しく動作"""
        tide_data = [
            (date(2026, 2, 9), TideType.SPRING),
            (date(2026, 2, 7), TideType.SPRING),
            (date(2026, 2, 8), TideType.SPRING),
        ]
        # 内部でソートされるため、中央日は2/8
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 7), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 8), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 9), tide_data) is False

    def test_different_tide_types_in_sequence(self) -> None:
        """異なる潮回りタイプが混在する場合"""
        tide_data = [
            (date(2026, 2, 1), TideType.YOUNG),
            (date(2026, 2, 2), TideType.YOUNG),
            (date(2026, 2, 3), TideType.LONG),
            (date(2026, 2, 4), TideType.LONG),
            (date(2026, 2, 5), TideType.LONG),
        ]
        # 若潮期間（2/1-2/2）の中央日は2/1（前半側）
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 1), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 2), tide_data) is False
        # 長潮期間（2/3-2/5）の中央日は2/4
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 3), tide_data) is False
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 4), tide_data) is True
        assert TidePeriodAnalyzer.is_midpoint_day(date(2026, 2, 5), tide_data) is False
