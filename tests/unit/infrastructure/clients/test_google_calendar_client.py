"""Unit tests for GoogleCalendarClient.

このモジュールは GoogleCalendarClient のユニットテストを提供します。
Google Calendar API の呼び出しをモック化して、クライアントのロジックを検証します。
"""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)


class TestGoogleCalendarClient:
    """GoogleCalendarClient のユニットテスト"""

    @pytest.fixture
    def mock_credentials_path(self, tmp_path: Path) -> Path:
        """モック認証情報パスのフィクスチャ"""
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{"installed": {"client_id": "test"}}')
        return creds_path

    @pytest.fixture
    def mock_token_path(self, tmp_path: Path) -> Path:
        """モックトークンパスのフィクスチャ"""
        return tmp_path / "token.json"

    @pytest.fixture
    def client(self, mock_credentials_path: Path, mock_token_path: Path) -> GoogleCalendarClient:
        """クライアントのフィクスチャ"""
        return GoogleCalendarClient(
            credentials_path=str(mock_credentials_path), token_path=str(mock_token_path)
        )

    @pytest.fixture
    def authenticated_client(
        self, client: GoogleCalendarClient, mock_token_path: Path
    ) -> GoogleCalendarClient:
        """認証済みクライアントのフィクスチャ"""
        # トークンをモック化
        mock_token_path.write_text('{"token": "mock_token", "refresh_token": "mock_refresh"}')

        with (
            patch(
                "fishing_forecast_gcal.infrastructure.clients.google_calendar_client.Credentials"
            ),
            patch(
                "fishing_forecast_gcal.infrastructure.clients.google_calendar_client.build"
            ) as mock_build,
        ):
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            client._service = mock_service  # pyright: ignore[reportPrivateUsage]
            client._creds = MagicMock()  # pyright: ignore[reportPrivateUsage]
            return client

    # ========================================
    # イベント作成のテスト
    # ========================================

    def test_create_event_success(self, authenticated_client: GoogleCalendarClient) -> None:
        """正常系: 新規イベント作成"""
        # Arrange
        calendar_id = "test@calendar.com"
        event_id = "test-event-id"
        summary = "潮汐 横須賀 (大潮)"
        description = "[TIDE]\n満潮: 06:00"
        start_date = date(2026, 2, 8)
        end_date = date(2026, 2, 9)

        mock_event = {
            "id": event_id,
            "summary": summary,
            "description": description,
            "start": {"date": "2026-02-08"},
            "end": {"date": "2026-02-09"},
        }

        # Calendar API のモックを設定
        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_service.events().insert().execute.return_value = mock_event

        # Act
        result = authenticated_client.create_event(
            calendar_id=calendar_id,
            event_id=event_id,
            summary=summary,
            description=description,
            start_date=start_date,
            end_date=end_date,
        )

        # Assert
        assert result["id"] == event_id
        assert result["summary"] == summary
        # モックのチェーン呼び出しを確認
        call_args = mock_service.events.return_value.insert.call_args
        assert call_args[1]["calendarId"] == calendar_id
        assert call_args[1]["body"]["summary"] == summary
        assert call_args[1]["body"]["start"]["date"] == "2026-02-08"

    def test_create_event_idempotency(self, authenticated_client: GoogleCalendarClient) -> None:
        """正常系: 同じイベントIDで再作成（冪等性）"""
        # Arrange
        calendar_id = "test@calendar.com"
        event_id = "existing-event-id"

        mock_event = {"id": event_id, "summary": "Test Event"}
        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_service.events().insert().execute.return_value = mock_event

        # Act - 2回作成
        result1 = authenticated_client.create_event(
            calendar_id=calendar_id,
            event_id=event_id,
            summary="Test Event",
            description="Description",
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 9),
        )
        result2 = authenticated_client.create_event(
            calendar_id=calendar_id,
            event_id=event_id,
            summary="Test Event",
            description="Description",
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 9),
        )

        # Assert - 冪等性: 同じイベントIDで同じ結果が返る
        assert result1["id"] == event_id
        assert result2["id"] == event_id
        assert result1["summary"] == result2["summary"]

    # ========================================
    # イベント取得のテスト
    # ========================================

    def test_get_event_success(self, authenticated_client: GoogleCalendarClient) -> None:
        """正常系: 既存イベント取得"""
        # Arrange
        calendar_id = "test@calendar.com"
        event_id = "test-event-id"
        mock_event = {
            "id": event_id,
            "summary": "Test Event",
            "description": "Test Description",
        }

        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_service.events().get().execute.return_value = mock_event

        # Act
        result = authenticated_client.get_event(calendar_id=calendar_id, event_id=event_id)

        # Assert
        assert result is not None
        assert result["id"] == event_id
        assert result["summary"] == "Test Event"
        # モックのチェーン呼び出しを確認
        call_args = mock_service.events.return_value.get.call_args
        assert call_args[1]["calendarId"] == calendar_id
        assert call_args[1]["eventId"] == event_id

    def test_get_event_not_found(self, authenticated_client: GoogleCalendarClient) -> None:
        """正常系: 存在しないイベント（Noneを返す）"""
        # Arrange
        from googleapiclient.errors import HttpError

        calendar_id = "test@calendar.com"
        event_id = "non-existent-id"

        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        # 404エラーをシミュレート
        mock_response = Mock()
        mock_response.status = 404
        mock_service.events().get().execute.side_effect = HttpError(mock_response, b"Not Found")

        # Act
        result = authenticated_client.get_event(calendar_id=calendar_id, event_id=event_id)

        # Assert
        assert result is None
        # モック呼び出しがあったことを確認
        assert mock_service.events.return_value.get.called

    # ========================================
    # イベント更新のテスト
    # ========================================

    def test_update_event_success(self, authenticated_client: GoogleCalendarClient) -> None:
        """正常系: 既存イベント更新（summary更新）"""
        # Arrange
        calendar_id = "test@calendar.com"
        event_id = "test-event-id"

        existing_event = {
            "id": event_id,
            "summary": "Old Summary",
            "description": "Old Description",
            "start": {"date": "2026-02-08"},
            "end": {"date": "2026-02-09"},
        }

        updated_event = {
            "id": event_id,
            "summary": "New Summary",
            "description": "Old Description",
            "start": {"date": "2026-02-08"},
            "end": {"date": "2026-02-09"},
        }

        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_service.events().get().execute.return_value = existing_event
        mock_service.events().patch().execute.return_value = updated_event

        # Act
        result = authenticated_client.update_event(
            calendar_id=calendar_id, event_id=event_id, summary="New Summary"
        )

        # Assert
        assert result["summary"] == "New Summary"
        # モックのチェーン呼び出しを確認
        assert mock_service.events.return_value.get.called
        assert mock_service.events.return_value.patch.called
        call_args = mock_service.events.return_value.patch.call_args
        assert call_args[1]["calendarId"] == calendar_id
        assert call_args[1]["eventId"] == event_id
        assert call_args[1]["body"]["summary"] == "New Summary"

    def test_update_event_description_only(
        self, authenticated_client: GoogleCalendarClient
    ) -> None:
        """正常系: 既存イベント更新（description更新）"""
        # Arrange
        calendar_id = "test@calendar.com"
        event_id = "test-event-id"

        existing_event = {
            "id": event_id,
            "summary": "Summary",
            "description": "Old Description",
        }

        updated_event = {
            "id": event_id,
            "summary": "Summary",
            "description": "New Description",
        }

        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_service.events().get().execute.return_value = existing_event
        mock_service.events().patch().execute.return_value = updated_event

        # Act
        result = authenticated_client.update_event(
            calendar_id=calendar_id, event_id=event_id, description="New Description"
        )

        # Assert
        assert result["description"] == "New Description"

    def test_update_event_not_found(self, authenticated_client: GoogleCalendarClient) -> None:
        """異常系: 存在しないイベント更新"""
        # Arrange
        from googleapiclient.errors import HttpError

        calendar_id = "test@calendar.com"
        event_id = "non-existent-id"

        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_response = Mock()
        mock_response.status = 404
        mock_service.events().get().execute.side_effect = HttpError(mock_response, b"Not Found")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Event not found"):
            authenticated_client.update_event(
                calendar_id=calendar_id, event_id=event_id, summary="New Summary"
            )

    # ========================================
    # エラーハンドリングのテスト
    # ========================================

    def test_get_service_before_authentication(self, client: GoogleCalendarClient) -> None:
        """異常系: 認証前のサービス取得"""
        # Act & Assert
        with pytest.raises(RuntimeError, match="Calendar service not initialized"):
            client.get_service()

    def test_create_event_authentication_error(
        self, authenticated_client: GoogleCalendarClient
    ) -> None:
        """異常系: 認証エラー（401）"""
        # Arrange
        from googleapiclient.errors import HttpError

        calendar_id = "test@calendar.com"
        event_id = "test-event-id"

        mock_service = authenticated_client._service  # pyright: ignore[reportPrivateUsage]
        mock_response = Mock()
        mock_response.status = 401
        mock_service.events().insert().execute.side_effect = HttpError(
            mock_response, b"Unauthorized"
        )

        # Act & Assert
        with pytest.raises(HttpError) as exc_info:
            authenticated_client.create_event(
                calendar_id=calendar_id,
                event_id=event_id,
                summary="Test",
                description="Test",
                start_date=date(2026, 2, 8),
                end_date=date(2026, 2, 9),
            )

        assert exc_info.value.resp.status == 401
