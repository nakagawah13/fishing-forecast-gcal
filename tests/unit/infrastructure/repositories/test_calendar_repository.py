"""カレンダーリポジトリの単体テスト

GoogleCalendarClient をモック化して CalendarRepository の動作を検証します。
"""

from datetime import date
from typing import Any
from unittest.mock import MagicMock

import pytest

from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from fishing_forecast_gcal.infrastructure.repositories.calendar_repository import (
    CalendarRepository,
)


@pytest.fixture
def mock_client() -> MagicMock:
    """GoogleCalendarClient のモックを作成"""
    return MagicMock(spec=GoogleCalendarClient)


@pytest.fixture
def calendar_repository(mock_client: MagicMock) -> CalendarRepository:
    """CalendarRepository インスタンスを作成（モッククライアント使用）"""
    return CalendarRepository(
        client=mock_client, calendar_id="test-calendar-id", timezone="Asia/Tokyo"
    )


@pytest.fixture
def sample_calendar_event() -> CalendarEvent:
    """テスト用の CalendarEvent を作成"""
    return CalendarEvent(
        event_id="abc123",
        title="潮汐 横須賀 (大潮)",
        description="[TIDE]\\n- 満潮: 06:12 (162cm)\\n- 干潮: 12:34 (58cm)",
        date=date(2026, 2, 8),
        location_id="yokosuka",
    )


@pytest.fixture
def sample_api_event() -> dict[str, Any]:
    """テスト用の Google Calendar API 形式のイベントを作成"""
    return {
        "id": "abc123",
        "summary": "潮汐 横須賀 (大潮)",
        "description": "[TIDE]\\n- 満潮: 06:12 (162cm)\\n- 干潮: 12:34 (58cm)",
        "start": {"date": "2026-02-08", "timeZone": "Asia/Tokyo"},
        "end": {"date": "2026-02-09", "timeZone": "Asia/Tokyo"},
        "extendedProperties": {"private": {"location_id": "yokosuka"}},
    }


class TestGetEvent:
    """get_event メソッドのテスト"""

    def test_get_event_success(
        self,
        calendar_repository: CalendarRepository,
        mock_client: MagicMock,
        sample_api_event: dict[str, Any],
    ) -> None:
        """正常系: 既存イベントをCalendarEventに変換"""
        # モックの設定
        mock_client.get_event.return_value = sample_api_event

        # 実行
        result = calendar_repository.get_event("abc123")

        # 検証
        assert result is not None
        assert result.event_id == "abc123"
        assert result.title == "潮汐 横須賀 (大潮)"
        assert result.date == date(2026, 2, 8)
        assert result.location_id == "yokosuka"

        # モックが正しく呼ばれたか確認
        mock_client.get_event.assert_called_once_with("test-calendar-id", "abc123")

    def test_get_event_not_found(
        self, calendar_repository: CalendarRepository, mock_client: MagicMock
    ) -> None:
        """正常系: 存在しないイベント（Noneを返す）"""
        # モックの設定
        mock_client.get_event.return_value = None

        # 実行
        result = calendar_repository.get_event("nonexistent")

        # 検証
        assert result is None

        # モックが正しく呼ばれたか確認
        mock_client.get_event.assert_called_once_with("test-calendar-id", "nonexistent")

    def test_get_event_api_error(
        self, calendar_repository: CalendarRepository, mock_client: MagicMock
    ) -> None:
        """異常系: API呼び出し失敗（RuntimeError）"""
        # モックの設定
        mock_client.get_event.side_effect = Exception("API Error")

        # 実行と検証
        with pytest.raises(RuntimeError, match="Failed to get event"):
            calendar_repository.get_event("abc123")

    def test_get_event_missing_location_id(
        self,
        calendar_repository: CalendarRepository,
        mock_client: MagicMock,
        sample_api_event: dict[str, Any],
    ) -> None:
        """異常系: location_idが extendedProperties に存在しない"""
        # extendedProperties を削除
        invalid_event = sample_api_event.copy()
        invalid_event["extendedProperties"] = {"private": {}}

        # モックの設定
        mock_client.get_event.return_value = invalid_event

        # 実行と検証
        with pytest.raises(RuntimeError, match="Failed to get event"):
            calendar_repository.get_event("abc123")


class TestUpsertEvent:
    """upsert_event メソッドのテスト"""

    def test_upsert_event_create_new(
        self,
        calendar_repository: CalendarRepository,
        mock_client: MagicMock,
        sample_calendar_event: CalendarEvent,
    ) -> None:
        """正常系: 新規イベント作成（既存なし）"""
        # モックの設定
        mock_client.get_event.return_value = None  # 既存イベントなし

        # 実行
        calendar_repository.upsert_event(sample_calendar_event)

        # 検証: create_event が呼ばれる
        mock_client.create_event.assert_called_once()
        call_args = mock_client.create_event.call_args[1]
        assert call_args["calendar_id"] == "test-calendar-id"
        assert call_args["event_id"] == "abc123"
        assert call_args["summary"] == "潮汐 横須賀 (大潮)"
        assert call_args["start_date"] == date(2026, 2, 8)
        assert call_args["end_date"] == date(2026, 2, 9)
        assert call_args["extended_properties"] == {"location_id": "yokosuka"}

        # update_event は呼ばれない
        mock_client.update_event.assert_not_called()

    def test_upsert_event_update_existing(
        self,
        calendar_repository: CalendarRepository,
        mock_client: MagicMock,
        sample_calendar_event: CalendarEvent,
        sample_api_event: dict[str, Any],
    ) -> None:
        """正常系: 既存イベント更新（既存あり）"""
        # モックの設定
        mock_client.get_event.return_value = sample_api_event  # 既存イベントあり

        # 実行
        calendar_repository.upsert_event(sample_calendar_event)

        # 検証: update_event が呼ばれる
        mock_client.update_event.assert_called_once()
        call_args = mock_client.update_event.call_args[1]
        assert call_args["calendar_id"] == "test-calendar-id"
        assert call_args["event_id"] == "abc123"
        assert call_args["summary"] == "潮汐 横須賀 (大潮)"
        assert call_args["start_date"] == date(2026, 2, 8)
        assert call_args["end_date"] == date(2026, 2, 9)
        assert call_args["extended_properties"] == {"location_id": "yokosuka"}

        # create_event は呼ばれない
        mock_client.create_event.assert_not_called()

    def test_upsert_event_idempotent(
        self,
        calendar_repository: CalendarRepository,
        mock_client: MagicMock,
        sample_calendar_event: CalendarEvent,
        sample_api_event: dict[str, Any],
    ) -> None:
        """正常系: 冪等性（同じCalendarEventで複数回upsert）"""
        # モックの設定
        mock_client.get_event.return_value = sample_api_event  # 既存イベントあり

        # 複数回実行
        calendar_repository.upsert_event(sample_calendar_event)
        calendar_repository.upsert_event(sample_calendar_event)

        # 検証: update_event が2回呼ばれる（冪等操作）
        assert mock_client.update_event.call_count == 2

    def test_upsert_event_api_error(
        self,
        calendar_repository: CalendarRepository,
        mock_client: MagicMock,
        sample_calendar_event: CalendarEvent,
    ) -> None:
        """異常系: API呼び出し失敗（RuntimeError）"""
        # モックの設定
        mock_client.get_event.side_effect = Exception("API Error")

        # 実行と検証
        with pytest.raises(RuntimeError, match="Failed to upsert event"):
            calendar_repository.upsert_event(sample_calendar_event)


class TestListEvents:
    """list_events メソッドのテスト"""

    def test_list_events_placeholder(self, calendar_repository: CalendarRepository) -> None:
        """Phase 2 実装: 現在は空リストを返す"""
        result = calendar_repository.list_events(
            start_date=date(2026, 2, 1), end_date=date(2026, 2, 28), location_id="yokosuka"
        )

        # 空リストが返される
        assert result == []


class TestAPIFormatConversion:
    """API形式変換のテスト"""

    def test_convert_to_domain_model_success(
        self,
        calendar_repository: CalendarRepository,
        sample_api_event: dict[str, Any],
    ) -> None:
        """Google API形式 → CalendarEvent 変換"""
        result = calendar_repository._convert_to_domain_model(sample_api_event)  # pyright: ignore[reportPrivateUsage]

        assert result.event_id == "abc123"
        assert result.title == "潮汐 横須賀 (大潮)"
        assert result.date == date(2026, 2, 8)
        assert result.location_id == "yokosuka"

    def test_convert_to_domain_model_missing_field(
        self, calendar_repository: CalendarRepository
    ) -> None:
        """不正な形式のAPIレスポンス（必須フィールド欠落）"""
        invalid_event = {
            "id": "abc123",
            # "summary" が欠落
            "start": {"date": "2026-02-08"},
        }

        with pytest.raises(ValueError, match="Invalid API event format"):
            calendar_repository._convert_to_domain_model(invalid_event)  # pyright: ignore[reportPrivateUsage]

    def test_convert_to_domain_model_missing_location_id(
        self,
        calendar_repository: CalendarRepository,
        sample_api_event: dict[str, Any],
    ) -> None:
        """location_id が extendedProperties に存在しない"""
        invalid_event = sample_api_event.copy()
        invalid_event["extendedProperties"] = {"private": {}}

        with pytest.raises(ValueError, match="location_id not found"):
            calendar_repository._convert_to_domain_model(invalid_event)  # pyright: ignore[reportPrivateUsage]
