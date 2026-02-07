"""潮汐モデルのテスト"""

import dataclasses
from datetime import UTC, date, datetime

import pytest

from fishing_forecast_gcal.domain.models.tide import Tide, TideEvent, TideType


class TestTideType:
    """TideType Enumのテスト"""

    def test_all_tide_types_defined(self) -> None:
        """全ての潮回りが定義されていること"""
        expected_types = ["SPRING", "MODERATE", "NEAP", "LONG", "YOUNG"]
        actual_types = [t.name for t in TideType]
        assert set(actual_types) == set(expected_types)

    def test_tide_type_values_are_japanese(self) -> None:
        """潮回りの値が日本語であること"""
        assert TideType.SPRING.value == "大潮"
        assert TideType.MODERATE.value == "中潮"
        assert TideType.NEAP.value == "小潮"
        assert TideType.LONG.value == "長潮"
        assert TideType.YOUNG.value == "若潮"


class TestTideEvent:
    """TideEventモデルのテスト"""

    def test_create_valid_high_tide_event(self) -> None:
        """正常な満潮イベントを作成できること"""
        event = TideEvent(
            time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
        )
        assert event.time.hour == 6
        assert event.height_cm == 162.0
        assert event.event_type == "high"

    def test_create_valid_low_tide_event(self) -> None:
        """正常な干潮イベントを作成できること"""
        event = TideEvent(
            time=datetime(2026, 2, 8, 12, 34, tzinfo=UTC), height_cm=58.0, event_type="low"
        )
        assert event.time.hour == 12
        assert event.height_cm == 58.0
        assert event.event_type == "low"

    def test_height_cm_negative_raises_error(self) -> None:
        """負の潮位でエラーが発生すること"""
        with pytest.raises(ValueError, match="height_cm must be between 0 and 500"):
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=-10.0, event_type="high"
            )

    def test_height_cm_over_500_raises_error(self) -> None:
        """500cmを超える潮位でエラーが発生すること"""
        with pytest.raises(ValueError, match="height_cm must be between 0 and 500"):
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=501.0, event_type="high"
            )

    def test_time_without_timezone_raises_error(self) -> None:
        """timezoneなしの時刻でエラーが発生すること"""
        with pytest.raises(ValueError, match="time must be timezone-aware"):
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12),  # No timezone
                height_cm=162.0,
                event_type="high",
            )

    def test_invalid_event_type_raises_error(self) -> None:
        """不正なevent_typeでエラーが発生すること"""
        # Note: 型ヒントで制約されるが、実行時チェックも実施
        with pytest.raises(ValueError, match="event_type must be 'high' or 'low'"):
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC),
                height_cm=162.0,
                event_type="invalid",  # type: ignore
            )

    def test_tide_event_is_immutable(self) -> None:
        """TideEventが不変であること"""
        event = TideEvent(
            time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            event.height_cm = 200.0  # type: ignore


class TestTide:
    """Tideモデルのテスト"""

    def test_create_valid_tide(self) -> None:
        """正常な潮汐情報を作成できること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 12, 34, tzinfo=UTC), height_cm=58.0, event_type="low"
            ),
        ]
        tide = Tide(
            date=date(2026, 2, 8),
            tide_type=TideType.SPRING,
            events=events,
            prime_time_start=datetime(2026, 2, 8, 4, 12, tzinfo=UTC),
            prime_time_end=datetime(2026, 2, 8, 8, 12, tzinfo=UTC),
        )
        assert tide.date == date(2026, 2, 8)
        assert tide.tide_type == TideType.SPRING
        assert len(tide.events) == 2
        assert tide.prime_time_start is not None
        assert tide.prime_time_end is not None

    def test_empty_events_raises_error(self) -> None:
        """空のeventsでエラーが発生すること"""
        with pytest.raises(ValueError, match="events must not be empty"):
            Tide(date=date(2026, 2, 8), tide_type=TideType.SPRING, events=[])

    def test_events_not_in_chronological_order_raises_error(self) -> None:
        """時系列順でないeventsでエラーが発生すること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 12, 34, tzinfo=UTC), height_cm=58.0, event_type="low"
            ),
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
        ]
        with pytest.raises(ValueError, match="events must be in chronological order"):
            Tide(date=date(2026, 2, 8), tide_type=TideType.SPRING, events=events)

    def test_prime_time_start_only_raises_error(self) -> None:
        """prime_time_startのみ設定でエラーが発生すること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
        ]
        with pytest.raises(
            ValueError, match="prime_time_start and prime_time_end must be both set or both None"
        ):
            Tide(
                date=date(2026, 2, 8),
                tide_type=TideType.SPRING,
                events=events,
                prime_time_start=datetime(2026, 2, 8, 4, 12, tzinfo=UTC),
                prime_time_end=None,
            )

    def test_prime_time_end_only_raises_error(self) -> None:
        """prime_time_endのみ設定でエラーが発生すること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
        ]
        with pytest.raises(
            ValueError, match="prime_time_start and prime_time_end must be both set or both None"
        ):
            Tide(
                date=date(2026, 2, 8),
                tide_type=TideType.SPRING,
                events=events,
                prime_time_start=None,
                prime_time_end=datetime(2026, 2, 8, 8, 12, tzinfo=UTC),
            )

    def test_prime_time_start_after_end_raises_error(self) -> None:
        """prime_time_start >= prime_time_endでエラーが発生すること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
        ]
        with pytest.raises(ValueError, match="prime_time_start must be before prime_time_end"):
            Tide(
                date=date(2026, 2, 8),
                tide_type=TideType.SPRING,
                events=events,
                prime_time_start=datetime(2026, 2, 8, 8, 12, tzinfo=UTC),
                prime_time_end=datetime(2026, 2, 8, 4, 12, tzinfo=UTC),
            )

    def test_tide_without_prime_time_is_valid(self) -> None:
        """prime_timeなしの潮汐情報が有効であること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
        ]
        tide = Tide(date=date(2026, 2, 8), tide_type=TideType.SPRING, events=events)
        assert tide.prime_time_start is None
        assert tide.prime_time_end is None

    def test_tide_is_immutable(self) -> None:
        """Tideが不変であること"""
        events = [
            TideEvent(
                time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC), height_cm=162.0, event_type="high"
            ),
        ]
        tide = Tide(date=date(2026, 2, 8), tide_type=TideType.SPRING, events=events)
        with pytest.raises(dataclasses.FrozenInstanceError):
            tide.tide_type = TideType.NEAP  # type: ignore
