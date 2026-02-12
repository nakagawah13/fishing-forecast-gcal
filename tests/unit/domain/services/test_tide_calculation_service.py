"""Unit tests for TideCalculationService.

TideCalculationService のユニットテスト。
"""

import math
from datetime import UTC, datetime, timedelta

from fishing_forecast_gcal.domain.services.tide_calculation_service import (
    TideCalculationService,
)


class TestTideCalculationService:
    """Test cases for TideCalculationService.

    TideCalculationService のテストクラス。
    """

    def test_extract_high_low_tides_from_typical_data(self) -> None:
        """Extract high and low tides from typical data.

        典型的な潮汐データから満干潮を抽出できることを確認します。
        """
        # Arrange: 典型的な1日の潮汐データ（1時間ごと）
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),  # 干潮に向かう
            (base_time.replace(hour=1), 80.0),
            (base_time.replace(hour=2), 60.0),  # 干潮
            (base_time.replace(hour=3), 80.0),
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 120.0),
            (base_time.replace(hour=6), 140.0),
            (base_time.replace(hour=7), 160.0),  # 満潮
            (base_time.replace(hour=8), 140.0),
            (base_time.replace(hour=9), 120.0),
            (base_time.replace(hour=10), 100.0),
            (base_time.replace(hour=11), 80.0),
            (base_time.replace(hour=12), 60.0),  # 干潮
            (base_time.replace(hour=13), 80.0),
            (base_time.replace(hour=14), 100.0),
            (base_time.replace(hour=15), 120.0),
            (base_time.replace(hour=16), 140.0),
            (base_time.replace(hour=17), 150.0),  # 満潮
            (base_time.replace(hour=18), 140.0),
            (base_time.replace(hour=19), 120.0),
            (base_time.replace(hour=20), 100.0),
            (base_time.replace(hour=21), 90.0),
            (base_time.replace(hour=22), 85.0),
            (base_time.replace(hour=23), 83.0),
        ]

        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 満潮2回、干潮2回が検出されること
        assert len(result) == 4

        # 時系列順に並んでいること
        assert result[0].time == base_time.replace(hour=2)
        assert result[0].event_type == "low"
        assert result[0].height_cm == 60.0

        assert result[1].time == base_time.replace(hour=7)
        assert result[1].event_type == "high"
        assert result[1].height_cm == 160.0

        assert result[2].time == base_time.replace(hour=12)
        assert result[2].event_type == "low"
        assert result[2].height_cm == 60.0

        assert result[3].time == base_time.replace(hour=17)
        assert result[3].event_type == "high"
        assert result[3].height_cm == 150.0

    def test_extract_high_low_tides_with_empty_data(self) -> None:
        """Return an empty list for empty data.

        空のデータから空リストを返すことを確認します。
        """
        # Arrange
        data: list[tuple[datetime, float]] = []
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_insufficient_data_one_point(self) -> None:
        """Return an empty list when only one point exists.

        データが1点のみの場合、空リストを返すことを確認します。
        """
        # Arrange
        data = [(datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC), 100.0)]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_insufficient_data_two_points(self) -> None:
        """Return an empty list when only two points exist.

        データが2点のみの場合、空リストを返すことを確認します。
        """
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time, 100.0),
            (base_time.replace(hour=1), 120.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_flat_data(self) -> None:
        """Return an empty list for completely flat data.

        全て同じ値のフラットなデータの場合、空リストを返すことを確認します。
        """
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [(base_time.replace(hour=i), 100.0) for i in range(24)]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_out_of_range_values(self) -> None:
        """Skip out-of-range tide extrema.

        範囲外の潮位を含む場合、その極値をスキップすることを確認します。
        """
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 80.0),
            (base_time.replace(hour=2), -10.0),  # 範囲外（負の値）
            (base_time.replace(hour=3), 80.0),
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 120.0),
            (base_time.replace(hour=6), 600.0),  # 範囲外（500cm超）
            (base_time.replace(hour=7), 120.0),
            (base_time.replace(hour=8), 100.0),
            (base_time.replace(hour=9), 80.0),
            (base_time.replace(hour=10), 60.0),  # 有効な干潮
            (base_time.replace(hour=11), 80.0),
            (base_time.replace(hour=12), 100.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 有効な極値（hour=10の干潮）のみ検出されること
        assert len(result) == 1
        assert result[0].time == base_time.replace(hour=10)
        assert result[0].event_type == "low"
        assert result[0].height_cm == 60.0

    def test_extract_high_low_tides_preserves_order(self) -> None:
        """Preserve chronological order in extracted events.

        抽出結果が時系列順に並んでいることを確認します。
        """
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 60.0),  # 干潮
            (base_time.replace(hour=2), 100.0),
            (base_time.replace(hour=3), 160.0),  # 満潮
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 50.0),  # 干潮
            (base_time.replace(hour=6), 100.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 時系列順であること
        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i].time < result[i + 1].time

    def test_extract_high_low_tides_with_multiple_peaks_in_sequence(self) -> None:
        """Handle consecutive extrema without dropping events.

        極値が連続する場合でも正しく検出できることを確認します。
        """
        # Arrange: ピークが連続するケース
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 120.0),  # 極大（満潮）
            (base_time.replace(hour=2), 100.0),  # 極小（干潮）
            (base_time.replace(hour=3), 110.0),  # 極大（満潮）
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 80.0),
            (base_time.replace(hour=6), 60.0),  # 極小（干潮）
            (base_time.replace(hour=7), 80.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 全ての極値が検出されること（満潮2回、干潮2回）
        assert len(result) == 4
        assert result[0].time == base_time.replace(hour=1)
        assert result[0].event_type == "high"
        assert result[1].time == base_time.replace(hour=2)
        assert result[1].event_type == "low"
        assert result[2].time == base_time.replace(hour=3)
        assert result[2].event_type == "high"
        assert result[3].time == base_time.replace(hour=6)
        assert result[3].event_type == "low"

    def test_extract_high_low_tides_with_flat_plateaus(self) -> None:
        """Detect high and low tides on flat plateaus.

        フラットな極値でも満干潮を検出できることを確認します。
        """
        # Arrange: 満潮・干潮がフラットになるケース
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 120.0),
            (base_time.replace(hour=2), 150.0),
            (base_time.replace(hour=3), 150.0),
            (base_time.replace(hour=4), 150.0),
            (base_time.replace(hour=5), 120.0),
            (base_time.replace(hour=6), 100.0),
            (base_time.replace(hour=7), 80.0),
            (base_time.replace(hour=8), 60.0),
            (base_time.replace(hour=9), 60.0),
            (base_time.replace(hour=10), 60.0),
            (base_time.replace(hour=11), 80.0),
            (base_time.replace(hour=12), 100.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: フラット区間の中央で満干潮が抽出されること
        assert len(result) == 2
        assert result[0].time == base_time.replace(hour=3)
        assert result[0].event_type == "high"
        assert result[1].time == base_time.replace(hour=9)
        assert result[1].event_type == "low"

    def test_extract_high_low_tides_detects_end_boundary_low(self) -> None:
        """Detect a low tide near the day boundary.

        日付境界付近の干潮が欠落しないことを確認します。
        """
        # Arrange: 終端側の極値が境界近くにあるケース
        base_time = datetime(2026, 2, 18, 23, 45, 0, tzinfo=UTC)
        data = [
            (base_time.replace(minute=45), 80.0),
            (base_time.replace(minute=50), 70.0),
            (base_time.replace(minute=55), 60.0),  # 干潮
            (base_time + timedelta(minutes=15), 70.0),  # 翌日00:00
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 境界付近の干潮が抽出されること
        assert len(result) == 1
        assert result[0].time == base_time.replace(minute=55)
        assert result[0].event_type == "low"

    def test_extract_high_low_tides_two_per_day_over_30_days(self) -> None:
        """Return two highs and two lows per day on a stable waveform.

        30日分の安定波形で各日2回ずつ満干潮が抽出されることを確認します。
        """
        # Arrange: 12時間周期の正弦波を1時間間隔で生成
        base_time = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
        total_hours = 30 * 24
        data: list[tuple[datetime, float]] = []
        for hour in range(total_hours):
            timestamp = base_time + timedelta(hours=hour)
            height = 100.0 + 50.0 * math.sin(2 * math.pi * (hour / 12.0))
            data.append((timestamp, height))

        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 日ごとに満潮2回・干潮2回が抽出されること
        counts_by_date: dict[str, dict[str, int]] = {}
        for event in result:
            day_key = event.time.date().isoformat()
            if day_key not in counts_by_date:
                counts_by_date[day_key] = {"high": 0, "low": 0}
            counts_by_date[day_key][event.event_type] += 1

        assert len(counts_by_date) == 30
        for counts in counts_by_date.values():
            assert counts["high"] == 2
            assert counts["low"] == 2


class TestCalculateTideRange:
    """Test cases for TideCalculationService.calculate_tide_range()."""

    def test_normal_tide_range(self) -> None:
        """Normal case: max high - min low."""
        from fishing_forecast_gcal.domain.models.tide import TideEvent

        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        events = [
            TideEvent(time=base.replace(hour=3), height_cm=150.0, event_type="high"),
            TideEvent(time=base.replace(hour=9), height_cm=50.0, event_type="low"),
            TideEvent(time=base.replace(hour=15), height_cm=160.0, event_type="high"),
            TideEvent(time=base.replace(hour=21), height_cm=55.0, event_type="low"),
        ]
        result = TideCalculationService.calculate_tide_range(events)
        # max_high=160 - min_low=50 = 110
        assert result == 110.0

    def test_no_high_tide_returns_zero(self) -> None:
        """Returns 0.0 when no high tide exists."""
        from fishing_forecast_gcal.domain.models.tide import TideEvent

        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        events = [
            TideEvent(time=base.replace(hour=9), height_cm=50.0, event_type="low"),
        ]
        assert TideCalculationService.calculate_tide_range(events) == 0.0

    def test_no_low_tide_returns_zero(self) -> None:
        """Returns 0.0 when no low tide exists."""
        from fishing_forecast_gcal.domain.models.tide import TideEvent

        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        events = [
            TideEvent(time=base.replace(hour=3), height_cm=150.0, event_type="high"),
        ]
        assert TideCalculationService.calculate_tide_range(events) == 0.0

    def test_empty_events_returns_zero(self) -> None:
        """Returns 0.0 when no events exist."""
        assert TideCalculationService.calculate_tide_range([]) == 0.0
