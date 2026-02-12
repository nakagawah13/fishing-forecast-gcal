"""カレンダーリポジトリの実装

このモジュールは ICalendarRepository インターフェースを実装し、
Google Calendar API を使用してカレンダーイベントの作成・取得・更新を行います。
"""

from datetime import date
from typing import Any

from ...domain.models.calendar_event import CalendarEvent
from ...domain.repositories.calendar_repository import ICalendarRepository
from ..clients.google_calendar_client import GoogleCalendarClient


class CalendarRepository(ICalendarRepository):
    """カレンダーリポジトリの実装

    Google Calendar API を使用してカレンダーイベントの作成・取得・更新を行います。
    冪等性を保証し、複数回実行しても結果が同じになるよう設計します。

    Attributes:
        client: GoogleCalendarClient インスタンス
        calendar_id: Google Calendar のカレンダーID
        timezone: タイムゾーン（デフォルト: Asia/Tokyo）
    """

    def __init__(
        self, client: GoogleCalendarClient, calendar_id: str, timezone: str = "Asia/Tokyo"
    ) -> None:
        """コンストラクタ

        Args:
            client: GoogleCalendarClient インスタンス
            calendar_id: Google Calendar のカレンダーID
            timezone: タイムゾーン（デフォルト: Asia/Tokyo）
        """
        self.client = client
        self.calendar_id = calendar_id
        self.timezone = timezone

    def get_event(self, event_id: str) -> CalendarEvent | None:
        """イベントIDでカレンダーイベントを取得

        Args:
            event_id: イベントID

        Returns:
            CalendarEvent | None: カレンダーイベント。存在しない場合は None

        Raises:
            RuntimeError: API呼び出しに失敗した場合
        """
        try:
            api_event = self.client.get_event(self.calendar_id, event_id)

            if api_event is None:
                return None

            # API形式からDomainモデルに変換
            return self._convert_to_domain_model(api_event)

        except Exception as e:
            raise RuntimeError(f"Failed to get event: {e}") from e

    def upsert_event(
        self,
        event: CalendarEvent,
        *,
        existing: CalendarEvent | None = None,
        attachments: list[dict[str, str]] | None = None,
    ) -> None:
        """Create or update a calendar event (idempotent).

        同一IDのイベントが存在する場合は更新、存在しない場合は新規作成します。

        Args:
            event (CalendarEvent): Event to create or update.
                                   (作成または更新するイベント)
            existing (CalendarEvent | None): Pre-fetched existing event.
                When provided, skips the internal get_event() call.
                Pass None (default) to let this method check existence itself.
                (事前取得済みの既存イベント。渡された場合は内部 get_event() をスキップ)
            attachments (list[dict[str, str]] | None): File attachments.
                Each dict should have 'fileUrl', 'title', 'mimeType' keys.
                (イベントに添付するファイル情報のリスト)

        Raises:
            RuntimeError: If API call fails (API呼び出しに失敗した場合).
        """
        try:
            # existing が明示的に渡されていない場合のみ内部で取得
            resolved_existing = existing if existing is not None else self.get_event(event.event_id)

            # extendedPropertiesにlocation_idを保存
            extended_props = {"location_id": event.location_id}

            if resolved_existing is not None:
                # 既存イベントを更新
                self.client.update_event(
                    calendar_id=self.calendar_id,
                    event_id=event.event_id,
                    summary=event.title,
                    description=event.description,
                    start_date=event.date,
                    end_date=self._get_next_day(event.date),
                    timezone=self.timezone,
                    extended_properties=extended_props,
                    attachments=attachments,
                )
            else:
                # 新規イベントを作成
                self.client.create_event(
                    calendar_id=self.calendar_id,
                    event_id=event.event_id,
                    summary=event.title,
                    description=event.description,
                    start_date=event.date,
                    end_date=self._get_next_day(event.date),
                    timezone=self.timezone,
                    extended_properties=extended_props,
                    attachments=attachments,
                )

        except Exception as e:
            raise RuntimeError(f"Failed to upsert event: {e}") from e

    def list_events(
        self, start_date: date, end_date: date, location_id: str
    ) -> list[CalendarEvent]:
        """List calendar events for a given period and location.

        指定期間・地点のカレンダーイベントのリストを取得します。

        Args:
            start_date: Search start date (inclusive)
            end_date: Search end date (inclusive)
            location_id: Immutable location ID

        Returns:
            list[CalendarEvent]: List of calendar events (empty list if none found)

        Raises:
            RuntimeError: If API call fails
        """
        try:
            api_events = self.client.list_events(
                calendar_id=self.calendar_id,
                start_date=start_date,
                end_date=end_date,
                private_extended_property=f"location_id={location_id}",
            )

            result: list[CalendarEvent] = []
            for api_event in api_events:
                try:
                    event = self._convert_to_domain_model(api_event)
                    result.append(event)
                except (ValueError, KeyError) as e:
                    import logging

                    logging.getLogger(__name__).warning("Skipping event with invalid format: %s", e)

            # Sort by date
            result.sort(key=lambda e: e.date)
            return result

        except Exception as e:
            raise RuntimeError(f"Failed to list events: {e}") from e

    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event by ID (idempotent).

        指定IDのカレンダーイベントを削除します。

        Args:
            event_id: Event ID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            RuntimeError: If API call fails
        """
        try:
            return self.client.delete_event(self.calendar_id, event_id)
        except Exception as e:
            raise RuntimeError(f"Failed to delete event: {e}") from e

    def _convert_to_domain_model(self, api_event: dict[str, Any]) -> CalendarEvent:
        """Google Calendar API形式をDomainモデルに変換

        Args:
            api_event: Google Calendar API形式のイベント

        Returns:
            CalendarEvent: Domainモデル

        Raises:
            KeyError: 必須フィールドが欠落している場合
            ValueError: 日付の解析に失敗した場合、またはlocation_idが取得できない場合
        """
        try:
            # 必須フィールドを取得
            event_id = api_event["id"]
            title = api_event["summary"]
            description = api_event.get("description", "")
            start_date_str = api_event["start"]["date"]

            # 日付を解析
            target_date = date.fromisoformat(start_date_str)

            # location_id を extendedProperties から取得
            extended_props = api_event.get("extendedProperties", {})
            private_props = extended_props.get("private", {})
            location_id = private_props.get("location_id", "")

            if not location_id:
                raise ValueError(
                    f"location_id not found in extendedProperties for event {event_id}"
                )

            return CalendarEvent(
                event_id=event_id,
                title=title,
                description=description,
                date=target_date,
                location_id=location_id,
            )

        except KeyError as e:
            raise ValueError(f"Invalid API event format: missing field {e}") from e

    @staticmethod
    def _get_next_day(target_date: date) -> date:
        """翌日の日付を取得

        終日イベントの終了日（exclusive）を取得するためのヘルパー関数。

        Args:
            target_date: 対象日

        Returns:
            date: 翌日の日付
        """
        from datetime import timedelta

        return target_date + timedelta(days=1)
