"""カレンダーリポジトリのインターフェース定義

このモジュールはGoogle カレンダーイベントの作成・取得・更新を抽象化します。
Infrastructure層で具体的な実装（Google Calendar API クライアント）を提供します。
"""

from abc import ABC, abstractmethod
from datetime import date

from ..models.calendar_event import CalendarEvent

__all__ = ["ICalendarRepository"]


class ICalendarRepository(ABC):
    """カレンダーリポジトリのインターフェース

    Google カレンダーイベントの作成・取得・更新を抽象化します。
    冪等性を保証し、複数回実行しても結果が同じになるよう設計します。

    Implementation Note:
        具体的な実装では、Google Calendar API を使用します。
        イベントIDは CalendarEvent.generate_event_id() で生成します。
    """

    @abstractmethod
    def get_event(self, event_id: str) -> CalendarEvent | None:
        """イベントIDでカレンダーイベントを取得

        Args:
            event_id: イベントID（CalendarEvent.generate_event_id() で生成）

        Returns:
            CalendarEvent | None: カレンダーイベント。存在しない場合は None

        Raises:
            RuntimeError: API呼び出しに失敗した場合（認証エラー、ネットワークエラー等）

        Note:
            - イベントIDは CalendarEvent.generate_event_id() で生成された安定ハッシュです
            - 同一の location_id + date の組み合わせは常に同じIDになります
        """
        ...

    @abstractmethod
    def upsert_event(
        self, event: CalendarEvent, *, existing: CalendarEvent | None = None
    ) -> None:
        """Create or update a calendar event (idempotent).

        同一IDのイベントが存在する場合は更新、存在しない場合は新規作成します。
        複数回実行しても結果が同じになることを保証します（冪等性）。

        Args:
            event (CalendarEvent): Event to create or update.
                                   (作成または更新するイベント)
            existing (CalendarEvent | None): Pre-fetched existing event, if available.
                When provided, skips the internal get_event() call to avoid
                a redundant API request. Pass None (default) to let upsert_event
                perform its own existence check.
                (事前取得済みの既存イベント。渡された場合は内部の get_event() をスキップ)

        Raises:
            RuntimeError: If API call fails (認証エラー、ネットワークエラー等).

        Note:
            - 既存イベントの NOTES セクションは保持されます
            - TIDE セクション、FORECAST セクションのみが更新されます
            - セクションが欠落している場合は更新をスキップし、ログで警告します
        """
        ...

    @abstractmethod
    def list_events(
        self, start_date: date, end_date: date, location_id: str
    ) -> list[CalendarEvent]:
        """List calendar events for a given period and location.

        指定期間・地点のカレンダーイベントのリストを取得します。
        既存イベントの取得や一括削除の対象特定に使用します。

        Args:
            start_date: Search start date (inclusive / 検索開始日（含む）)
            end_date: Search end date (inclusive / 検索終了日（含む）)
            location_id: Immutable location ID (地点の不変ID)

        Returns:
            list[CalendarEvent]: List of calendar events (empty list if none found)

        Raises:
            RuntimeError: If API call fails (認証エラー、ネットワークエラー等)

        Note:
            - Results are sorted by date (結果は日付順にソート)
            - Only events matching the location_id are returned
        """
        ...

    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event by ID (idempotent).

        指定IDのカレンダーイベントを削除します（冪等操作）。

        Args:
            event_id: Event ID to delete (CalendarEvent.generate_event_id() で生成)

        Returns:
            True if deleted successfully, False if event did not exist

        Raises:
            RuntimeError: If API call fails (認証エラー、ネットワークエラー等)
        """
        ...
