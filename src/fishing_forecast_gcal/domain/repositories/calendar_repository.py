"""カレンダーリポジトリのインターフェース定義

このモジュールはGoogle カレンダーイベントの作成・取得・更新を抽象化します。
Infrastructure層で具体的な実装（Google Calendar API クライアント）を提供します。
"""

from abc import ABC, abstractmethod
from datetime import date

from ..models.calendar_event import CalendarEvent


class ICalendarRepository(ABC):
    """カレンダーリポジトリのインターフェース

    Google カレンダーイベントの作成・取得・更新を抽象化します。
    冪等性を保証し、複数回実行しても結果が同じになるよう設計します。

    Implementation Note:
        具体的な実装では、Google Calendar API を使用します。
        イベントIDの生成ロジック（calendar_id + location_id + date のハッシュ化）は
        Infrastructure層で実装します。
    """

    @abstractmethod
    def get_event(self, event_id: str) -> CalendarEvent | None:
        """イベントIDでカレンダーイベントを取得

        Args:
            event_id: イベントID（calendar_id + location_id + date から生成されるハッシュ）

        Returns:
            CalendarEvent | None: カレンダーイベント。存在しない場合は None

        Raises:
            RuntimeError: API呼び出しに失敗した場合（認証エラー、ネットワークエラー等）

        Note:
            - イベントIDは安定ハッシュ（MD5等）で生成されます
            - 同一の calendar_id + location_id + date の組み合わせは常に同じIDになります
        """
        ...

    @abstractmethod
    def upsert_event(self, event: CalendarEvent) -> None:
        """カレンダーイベントを作成または更新（冪等操作）

        同一IDのイベントが存在する場合は更新、存在しない場合は新規作成します。
        複数回実行しても結果が同じになることを保証します（冪等性）。

        Args:
            event: 作成または更新するイベント

        Raises:
            RuntimeError: API呼び出しに失敗した場合（認証エラー、ネットワークエラー等）

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
        """指定期間・地点のカレンダーイベントのリストを取得

        Phase 2（予報更新機能）で使用します。
        既存イベントを取得し、予報セクションのみを更新するために使用します。

        Args:
            start_date: 検索開始日（含む）
            end_date: 検索終了日（含む）
            location_id: 地点の不変ID

        Returns:
            list[CalendarEvent]: カレンダーイベントのリスト（空リスト可）

        Raises:
            RuntimeError: API呼び出しに失敗した場合（認証エラー、ネットワークエラー等）

        Note:
            - 結果は日付順にソートされます
            - 指定地点のイベントのみが返されます（location_idでフィルタ）
        """
        ...
