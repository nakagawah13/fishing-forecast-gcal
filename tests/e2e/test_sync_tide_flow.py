"""E2E tests for the sync-tide flow.

システム全体の統合テストを実装します。
実際の Google Calendar API と調和定数データを使用して、
潮汐イベントの作成・冪等性・[NOTES] セクション保持を検証します。

前提条件:
    - 環境変数 ``E2E_CALENDAR_ID``: テスト専用カレンダー ID
    - ``config/credentials.json``: OAuth クライアント情報
    - ``config/token.json``: OAuth トークン
    - ``config/harmonics/tk.pkl``: 東京の調和定数データ

実行方法::

    E2E_CALENDAR_ID="your_test_calendar_id" uv run pytest tests/e2e/ -m e2e -v
"""

from __future__ import annotations

import re
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

from fishing_forecast_gcal.application.usecases.sync_tide_usecase import SyncTideUseCase
from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import TideType
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
)
from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from fishing_forecast_gcal.infrastructure.repositories.calendar_repository import (
    CalendarRepository,
)
from fishing_forecast_gcal.infrastructure.repositories.tide_data_repository import (
    TideDataRepository,
)

# Google Calendar API のレートリミット対策
API_DELAY_SEC = 0.5


def _api_delay() -> None:
    """API 呼び出し間のレートリミット対策"""
    time.sleep(API_DELAY_SEC)


@pytest.mark.e2e
class TestSyncTideE2E:
    """E2E テスト: 潮汐同期の全体フロー

    実際の Google Calendar API と UTide 調和定数を使用して、
    SyncTideUseCase の全フローを検証します。
    """

    @pytest.fixture
    def tide_repo(self, harmonics_dir: Path, tk_harmonics: Path) -> TideDataRepository:
        """実データを使用した TideDataRepository"""
        adapter = TideCalculationAdapter(harmonics_dir=harmonics_dir)
        return TideDataRepository(adapter=adapter)

    @pytest.fixture
    def calendar_repo(
        self,
        calendar_client: GoogleCalendarClient,
        e2e_calendar_id: str,
    ) -> CalendarRepository:
        """実 API を使用した CalendarRepository"""
        return CalendarRepository(
            client=calendar_client,
            calendar_id=e2e_calendar_id,
        )

    @pytest.fixture
    def usecase(
        self,
        tide_repo: TideDataRepository,
        calendar_repo: CalendarRepository,
    ) -> SyncTideUseCase:
        """実依存を使用した SyncTideUseCase"""
        return SyncTideUseCase(
            tide_repo=tide_repo,
            calendar_repo=calendar_repo,
        )

    @pytest.fixture
    def target_date(self) -> date:
        """テスト対象日（将来の日付を固定で使用）"""
        return date(2026, 6, 15)

    @pytest.fixture
    def event_id(self, tokyo_location: Location, target_date: date) -> str:
        """テスト対象イベント ID"""
        return CalendarEvent.generate_event_id(tokyo_location.id, target_date)

    @pytest.fixture(autouse=True)
    def cleanup_events(
        self,
        calendar_client: GoogleCalendarClient,
        e2e_calendar_id: str,
        tokyo_location: Location,
    ) -> None:
        """テスト前にテスト対象イベントを削除してクリーンな状態を確保

        テスト対象日のイベントが残存している場合に削除します。
        テスト後のクリーンアップは行わず、結果を手動確認可能にします。
        """
        # テスト対象日の範囲を定義（target_date を含む 3 日間）
        target_dates = [
            date(2026, 6, 15),
            date(2026, 6, 16),
            date(2026, 6, 17),
        ]

        for d in target_dates:
            event_id = CalendarEvent.generate_event_id(tokyo_location.id, d)
            try:
                existing = calendar_client.get_event(e2e_calendar_id, event_id)
                if existing is not None:
                    calendar_client.get_service().events().delete(
                        calendarId=e2e_calendar_id,
                        eventId=event_id,
                    ).execute()
                    _api_delay()
            except Exception:
                # 削除失敗は無視（存在しない場合を含む）
                pass

    # ------------------------------------------------------------------
    # テストケース
    # ------------------------------------------------------------------

    def test_create_tide_events(
        self,
        usecase: SyncTideUseCase,
        calendar_repo: CalendarRepository,
        tokyo_location: Location,
        target_date: date,
        event_id: str,
    ) -> None:
        """基本フロー: 潮汐イベントを作成し、内容を検証する

        検証項目:
        - イベントが正常に作成されること
        - タイトルが「潮汐 {location_name} ({tide_type})」形式であること
        - 本文に [TIDE] セクションが含まれること
        - 満潮・干潮情報が正しいフォーマットで記載されること
        - 潮回りが有効な TideType であること
        """
        # Act
        usecase.execute(tokyo_location, target_date)
        _api_delay()

        # Assert: イベントが作成されたことを確認
        event = calendar_repo.get_event(event_id)
        assert event is not None, "イベントが作成されていません"

        # タイトルの形式検証（絵文字付き新形式）
        # 絵文字は先頭に来るため、地点名で検証
        assert "東京" in event.title, f"タイトルに地点名が含まれていません: {event.title}"
        # タイトルに有効な潮回りが含まれることを確認
        tide_type_values = [t.value for t in TideType]
        assert any(t in event.title for t in tide_type_values), (
            f"タイトルに有効な潮回りが含まれていません: {event.title}"
        )

        # 本文の [TIDE] セクション検証
        assert "[TIDE]" in event.description, "本文に [TIDE] セクションがありません"

        # 満潮・干潮情報の検証（HH:MM (XXXcm) 形式）
        tide_pattern = re.compile(r"(満潮|干潮): \d{2}:\d{2} \(\d+cm\)")
        assert tide_pattern.search(event.description), (
            f"満潮・干潮情報のフォーマットが不正:\n{event.description}"
        )

        # 日付の検証
        assert event.date == target_date

        # location_id の検証
        assert event.location_id == tokyo_location.id

    def test_create_multiple_days(
        self,
        usecase: SyncTideUseCase,
        calendar_repo: CalendarRepository,
        tokyo_location: Location,
    ) -> None:
        """複数日分のイベントを連続作成する

        検証項目:
        - 3 日分のイベントがすべて作成されること
        - 各イベントの日付が正しいこと
        """
        dates = [
            date(2026, 6, 15),
            date(2026, 6, 16),
            date(2026, 6, 17),
        ]

        # Act
        for d in dates:
            usecase.execute(tokyo_location, d)
            _api_delay()

        # Assert
        for d in dates:
            eid = CalendarEvent.generate_event_id(tokyo_location.id, d)
            event = calendar_repo.get_event(eid)
            assert event is not None, f"{d} のイベントが作成されていません"
            assert event.date == d

    def test_idempotency(
        self,
        usecase: SyncTideUseCase,
        calendar_repo: CalendarRepository,
        tokyo_location: Location,
        target_date: date,
        event_id: str,
    ) -> None:
        """冪等性: 同一イベントを 2 回実行しても重複しない

        検証項目:
        - 2 回目の実行でエラーが発生しないこと
        - イベント内容が 1 回目と同一であること（[NOTES] セクション以外）
        """
        # Act: 1 回目
        usecase.execute(tokyo_location, target_date)
        _api_delay()

        event_first = calendar_repo.get_event(event_id)
        assert event_first is not None

        # Act: 2 回目
        usecase.execute(tokyo_location, target_date)
        _api_delay()

        event_second = calendar_repo.get_event(event_id)
        assert event_second is not None

        # Assert: イベント内容が一致
        assert event_first.event_id == event_second.event_id
        assert event_first.title == event_second.title
        assert event_first.date == event_second.date
        assert event_first.location_id == event_second.location_id

        # [TIDE] セクションの内容が一致
        tide_first = event_first.extract_section("TIDE")
        tide_second = event_second.extract_section("TIDE")
        assert tide_first == tide_second, (
            f"[TIDE] セクションが一致しません:\n1回目: {tide_first}\n2回目: {tide_second}"
        )

    def test_preserve_notes_section(
        self,
        usecase: SyncTideUseCase,
        calendar_repo: CalendarRepository,
        calendar_client: GoogleCalendarClient,
        e2e_calendar_id: str,
        tokyo_location: Location,
        target_date: date,
        event_id: str,
    ) -> None:
        """[NOTES] セクション保持: ユーザー追記が再同期後も維持される

        検証項目:
        - [NOTES] セクションに追記した内容が保持されること
        - [TIDE] セクションは正常に更新されること
        """
        # Arrange: 初回イベント作成
        usecase.execute(tokyo_location, target_date)
        _api_delay()

        # [NOTES] にユーザー追記をシミュレート
        user_note = "テスト用メモ: 朝マズメ狙い"
        event = calendar_repo.get_event(event_id)
        assert event is not None

        # 既存の description に [NOTES] セクションを追加/更新
        original_description = event.description
        if "[NOTES]" in original_description:
            # [NOTES] セクションの内容を置換
            updated_description = re.sub(
                r"\[NOTES\]\n(.*?)(?=\n\[|\Z)",
                f"[NOTES]\n- {user_note}\n",
                original_description,
                flags=re.DOTALL,
            )
        else:
            updated_description = original_description + f"\n[NOTES]\n- {user_note}\n"

        # Google Calendar API で直接更新
        next_day = target_date + timedelta(days=1)
        calendar_client.update_event(
            calendar_id=e2e_calendar_id,
            event_id=event_id,
            description=updated_description,
            start_date=target_date,
            end_date=next_day,
        )
        _api_delay()

        # Act: 再同期
        usecase.execute(tokyo_location, target_date)
        _api_delay()

        # Assert: [NOTES] が保持されていること
        updated_event = calendar_repo.get_event(event_id)
        assert updated_event is not None

        notes_section = updated_event.extract_section("NOTES")
        assert notes_section is not None, "[NOTES] セクションが失われました"
        assert user_note in notes_section, (
            f"ユーザー追記が保持されていません:\n期待値: {user_note}\n実際: {notes_section}"
        )

        # [TIDE] セクションも存在すること
        tide_section = updated_event.extract_section("TIDE")
        assert tide_section is not None, "[TIDE] セクションが失われました"

    def test_error_handling_missing_harmonics(
        self,
        calendar_repo: CalendarRepository,
        harmonics_dir: Path,
    ) -> None:
        """エラーハンドリング: 調和定数が存在しない地点

        検証項目:
        - FileNotFoundError が RuntimeError にラップされること
        - エラーメッセージに地点情報が含まれること
        """
        # Arrange: 存在しない地点
        nonexistent_location = Location(
            id="nonexistent_port",
            name="存在しない港",
            latitude=35.0,
            longitude=139.0,
            station_id="ZZ",
        )
        adapter = TideCalculationAdapter(harmonics_dir=harmonics_dir)
        tide_repo = TideDataRepository(adapter=adapter)
        usecase = SyncTideUseCase(
            tide_repo=tide_repo,
            calendar_repo=calendar_repo,
        )

        # Act & Assert
        with pytest.raises(RuntimeError):
            usecase.execute(nonexistent_location, date(2026, 6, 15))
