"""Unit tests for ResetTideUseCase.

ResetTideUseCase の単体テストです。
カレンダーリポジトリをモック化して削除ロジックを検証します。
"""

from datetime import date
from unittest.mock import MagicMock

import pytest

from fishing_forecast_gcal.application.usecases.reset_tide_usecase import (
    ResetResult,
    ResetTideUseCase,
)
from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.repositories.calendar_repository import ICalendarRepository


@pytest.fixture
def mock_calendar_repo() -> MagicMock:
    """Mock ICalendarRepository instance."""
    return MagicMock(spec=ICalendarRepository)


@pytest.fixture
def reset_usecase(mock_calendar_repo: MagicMock) -> ResetTideUseCase:
    """ResetTideUseCase instance with mock repository."""
    return ResetTideUseCase(calendar_repo=mock_calendar_repo)


@pytest.fixture
def sample_location() -> Location:
    """Test location fixture."""
    return Location(
        id="tk",
        name="東京",
        latitude=35.650,
        longitude=139.770,
        station_id="TK",
    )


@pytest.fixture
def sample_events() -> list[CalendarEvent]:
    """Test calendar events fixture."""
    return [
        CalendarEvent(
            event_id="event1",
            title="🔴東京 (大潮)",
            description="[TIDE]\ntest",
            date=date(2026, 2, 8),
            location_id="tk",
        ),
        CalendarEvent(
            event_id="event2",
            title="🟠東京 (中潮)",
            description="[TIDE]\ntest",
            date=date(2026, 2, 9),
            location_id="tk",
        ),
        CalendarEvent(
            event_id="event3",
            title="🔵東京 (小潮)",
            description="[TIDE]\ntest",
            date=date(2026, 2, 10),
            location_id="tk",
        ),
    ]


class TestResetTideUseCase:
    """ResetTideUseCase tests."""

    def test_execute_deletes_all_events(
        self,
        reset_usecase: ResetTideUseCase,
        mock_calendar_repo: MagicMock,
        sample_location: Location,
        sample_events: list[CalendarEvent],
    ) -> None:
        """Normal: deletes all found events. (正常系: 全イベント削除)"""
        mock_calendar_repo.list_events.return_value = sample_events
        mock_calendar_repo.delete_event.return_value = True

        result = reset_usecase.execute(
            location=sample_location,
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 10),
        )

        assert result == ResetResult(total_found=3, total_deleted=3, total_failed=0)
        assert mock_calendar_repo.delete_event.call_count == 3
        mock_calendar_repo.list_events.assert_called_once_with(
            date(2026, 2, 8), date(2026, 2, 10), "tk"
        )

    def test_execute_no_events_found(
        self,
        reset_usecase: ResetTideUseCase,
        mock_calendar_repo: MagicMock,
        sample_location: Location,
    ) -> None:
        """Normal: no events to delete. (正常系: 削除対象なし)"""
        mock_calendar_repo.list_events.return_value = []

        result = reset_usecase.execute(
            location=sample_location,
            start_date=date(2026, 6, 1),
            end_date=date(2026, 6, 30),
        )

        assert result == ResetResult(total_found=0, total_deleted=0, total_failed=0)
        mock_calendar_repo.delete_event.assert_not_called()

    def test_execute_dry_run(
        self,
        reset_usecase: ResetTideUseCase,
        mock_calendar_repo: MagicMock,
        sample_location: Location,
        sample_events: list[CalendarEvent],
    ) -> None:
        """Normal: dry-run does not delete. (正常系: dry-run では削除しない)"""
        mock_calendar_repo.list_events.return_value = sample_events

        result = reset_usecase.execute(
            location=sample_location,
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 10),
            dry_run=True,
        )

        assert result == ResetResult(total_found=3, total_deleted=0, total_failed=0)
        mock_calendar_repo.delete_event.assert_not_called()

    def test_execute_partial_failure(
        self,
        reset_usecase: ResetTideUseCase,
        mock_calendar_repo: MagicMock,
        sample_location: Location,
        sample_events: list[CalendarEvent],
    ) -> None:
        """Normal: partial deletion failure. (正常系: 一部削除失敗)"""
        mock_calendar_repo.list_events.return_value = sample_events
        # First succeeds, second fails, third succeeds
        mock_calendar_repo.delete_event.side_effect = [
            True,
            RuntimeError("API Error"),
            True,
        ]

        result = reset_usecase.execute(
            location=sample_location,
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 10),
        )

        assert result == ResetResult(total_found=3, total_deleted=2, total_failed=1)

    def test_execute_event_already_deleted(
        self,
        reset_usecase: ResetTideUseCase,
        mock_calendar_repo: MagicMock,
        sample_location: Location,
        sample_events: list[CalendarEvent],
    ) -> None:
        """Normal: already deleted events count as success. (正常系: 既削除はカウント)"""
        mock_calendar_repo.list_events.return_value = sample_events
        # delete_event returns False for already-deleted events
        mock_calendar_repo.delete_event.return_value = False

        result = reset_usecase.execute(
            location=sample_location,
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 10),
        )

        # All count as deleted (idempotent)
        assert result == ResetResult(total_found=3, total_deleted=3, total_failed=0)


class TestResetResult:
    """ResetResult model tests."""

    def test_reset_result_frozen(self) -> None:
        """Frozen dataclass cannot be modified."""
        result = ResetResult(total_found=3, total_deleted=2, total_failed=1)

        with pytest.raises(AttributeError):
            result.total_found = 5  # type: ignore[misc]
