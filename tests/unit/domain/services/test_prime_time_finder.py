"""時合い帯特定サービスのテスト"""

from datetime import UTC, datetime

import pytest

from fishing_forecast_gcal.domain.models.tide import TideEvent
from fishing_forecast_gcal.domain.services.prime_time_finder import PrimeTimeFinder


class TestPrimeTimeFinder:
    """PrimeTimeFinderのテスト"""

    @pytest.fixture
    def finder(self) -> PrimeTimeFinder:
        """PrimeTimeFinderインスタンス"""
        return PrimeTimeFinder()

    def test_find_basic_case(self, finder: PrimeTimeFinder) -> None:
        """基本ケース: 12:00満潮 → (10:00, 14:00)"""
        # 2026-02-08 12:00 UTC の満潮
        high_tide_time = datetime(2026, 2, 8, 12, 0, tzinfo=UTC)
        events = [
            TideEvent(time=high_tide_time, height_cm=180.0, event_type="high"),
        ]

        result = finder.find(events)

        assert result is not None
        start, end = result
        assert start == datetime(2026, 2, 8, 10, 0, tzinfo=UTC)
        assert end == datetime(2026, 2, 8, 14, 0, tzinfo=UTC)

    def test_find_with_multiple_high_tides(self, finder: PrimeTimeFinder) -> None:
        """複数満潮: 06:00満潮, 18:00満潮 → 最初の満潮(06:00)を使用"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                height_cm=170.0,
                event_type="high",
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 12, 0, tzinfo=UTC),
                height_cm=50.0,
                event_type="low",
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 18, 0, tzinfo=UTC),
                height_cm=180.0,
                event_type="high",
            ),
        ]

        result = finder.find(events)

        assert result is not None
        start, end = result
        # 最初の満潮(06:00)から±2時間
        assert start == datetime(2026, 2, 8, 4, 0, tzinfo=UTC)
        assert end == datetime(2026, 2, 8, 8, 0, tzinfo=UTC)

    def test_find_crosses_date_boundary_before_midnight(self, finder: PrimeTimeFinder) -> None:
        """日付跨ぎ（前）: 01:00満潮 → (前日23:00, 03:00)"""
        high_tide_time = datetime(2026, 2, 8, 1, 0, tzinfo=UTC)
        events = [
            TideEvent(time=high_tide_time, height_cm=180.0, event_type="high"),
        ]

        result = finder.find(events)

        assert result is not None
        start, end = result
        # 前日の23:00
        assert start == datetime(2026, 2, 7, 23, 0, tzinfo=UTC)
        assert end == datetime(2026, 2, 8, 3, 0, tzinfo=UTC)

    def test_find_crosses_date_boundary_after_midnight(self, finder: PrimeTimeFinder) -> None:
        """日付跨ぎ（後）: 23:00満潮 → (21:00, 翌日01:00)"""
        high_tide_time = datetime(2026, 2, 8, 23, 0, tzinfo=UTC)
        events = [
            TideEvent(time=high_tide_time, height_cm=180.0, event_type="high"),
        ]

        result = finder.find(events)

        assert result is not None
        start, end = result
        assert start == datetime(2026, 2, 8, 21, 0, tzinfo=UTC)
        # 翌日の01:00
        assert end == datetime(2026, 2, 9, 1, 0, tzinfo=UTC)

    def test_find_no_high_tide(self, finder: PrimeTimeFinder) -> None:
        """満潮なし: 干潮のみ → None"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                height_cm=50.0,
                event_type="low",
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 18, 0, tzinfo=UTC),
                height_cm=60.0,
                event_type="low",
            ),
        ]

        result = finder.find(events)

        assert result is None

    def test_find_empty_events(self, finder: PrimeTimeFinder) -> None:
        """空リスト: [] → None"""
        events: list[TideEvent] = []

        result = finder.find(events)

        assert result is None

    def test_find_with_mixed_events(self, finder: PrimeTimeFinder) -> None:
        """満干潮混在: 干潮→満潮→干潮の順序で最初の満潮を使用"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 3, 0, tzinfo=UTC),
                height_cm=30.0,
                event_type="low",
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 9, 30, tzinfo=UTC),
                height_cm=190.0,
                event_type="high",
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 15, 45, tzinfo=UTC),
                height_cm=40.0,
                event_type="low",
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 22, 0, tzinfo=UTC),
                height_cm=185.0,
                event_type="high",
            ),
        ]

        result = finder.find(events)

        assert result is not None
        start, end = result
        # 09:30の満潮から±2時間
        assert start == datetime(2026, 2, 8, 7, 30, tzinfo=UTC)
        assert end == datetime(2026, 2, 8, 11, 30, tzinfo=UTC)
