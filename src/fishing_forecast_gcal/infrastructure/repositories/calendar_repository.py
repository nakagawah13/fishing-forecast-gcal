"""カレンダーリポジトリの実装

このモジュールは ICalendarRepository インターフェースを実装し、
Google Calendar API を使用してカレンダーイベントの作成・取得・更新を行います。
"""

import hashlib
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

    @staticmethod
    def generate_event_id(calendar_id: str, location_id: str, target_date: date) -> str:
        """イベントIDを生成

        calendar_id + location_id + date を素材に MD5 ハッシュで安定IDを生成します。
        同じ入力からは常に同じIDが生成されます（冪等性）。

        Args:
            calendar_id: カレンダーID
            location_id: 地点の不変ID
            target_date: 対象日

        Returns:
            str: イベントID（MD5ハッシュ、32文字）

        Note:
            Google Calendar API の制約:
            - 5-1024文字
            - 英数字とハイフン（-）のみ
            - 大文字小文字を区別

            MD5ハッシュ（32文字）は制約を満たします。
        """
        # calendar_id + location_id + date を結合
        source = f"{calendar_id}_{location_id}_{target_date.isoformat()}"

        # MD5ハッシュで安定IDを生成
        event_id = hashlib.md5(source.encode("utf-8")).hexdigest()

        return event_id

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

    def upsert_event(self, event: CalendarEvent) -> None:
        """カレンダーイベントを作成または更新（冪等操作）

        同一IDのイベントが存在する場合は更新、存在しない場合は新規作成します。

        Args:
            event: 作成または更新するイベント

        Raises:
            RuntimeError: API呼び出しに失敗した場合
        """
        try:
            # 既存イベントを確認
            existing_event = self.get_event(event.event_id)

            # extendedPropertiesにlocation_idを保存
            extended_props = {"location_id": event.location_id}

            if existing_event is not None:
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
                )

        except Exception as e:
            raise RuntimeError(f"Failed to upsert event: {e}") from e

    def list_events(
        self, start_date: date, end_date: date, location_id: str
    ) -> list[CalendarEvent]:
        """指定期間・地点のカレンダーイベントのリストを取得

        Args:
            start_date: 検索開始日（含む）
            end_date: 検索終了日（含む）
            location_id: 地点の不変ID

        Returns:
            list[CalendarEvent]: カレンダーイベントのリスト（空リスト可）

        Raises:
            RuntimeError: API呼び出しに失敗した場合

        Note:
            フェーズ2（予報更新機能）で使用します。
            今回はプレースホルダー実装として空リストを返します。
        """
        # TODO: Phase 2 で実装
        return []

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
                raise ValueError(f"location_id not found in extendedProperties for event {event_id}")

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
