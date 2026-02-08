"""カレンダーリポジトリインターフェースのテスト

ICalendarRepository の抽象基底クラスとしての振る舞いをテストします。
"""

from datetime import date
from typing import override

import pytest

from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.domain.repositories.calendar_repository import (
    ICalendarRepository,
)


class TestICalendarRepositoryAbstract:
    """抽象基底クラスとしての振る舞いをテスト"""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """抽象基底クラスを直接インスタンス化できないことを確認"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ICalendarRepository()  # type: ignore[abstract]

    def test_cannot_instantiate_incomplete_subclass(self) -> None:
        """抽象メソッドを実装していないサブクラスはインスタンス化できないことを確認"""

        class IncompleteRepository(ICalendarRepository):
            """一部のメソッドのみ実装した不完全なサブクラス"""

            @override
            def get_event(self, event_id: str) -> CalendarEvent | None:
                return None

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteRepository()  # type: ignore[abstract]


class TestICalendarRepositoryMock:
    """Mock実装を使った動作テスト"""

    def test_mock_implementation_works(self) -> None:
        """Mock実装が正しく動作することを確認"""

        class MockCalendarRepository(ICalendarRepository):
            """テスト用のMock実装"""

            def __init__(self) -> None:
                self.events: dict[str, CalendarEvent] = {}

            @override
            def get_event(self, event_id: str) -> CalendarEvent | None:
                """イベントを取得"""
                return self.events.get(event_id)

            @override
            def generate_event_id_for_location_date(
                self, location_id: str, target_date: date
            ) -> str:
                """イベントIDを生成"""
                return f"{location_id}_{target_date.isoformat()}"

            @override
            def upsert_event(self, event: CalendarEvent) -> None:
                """イベントを作成または更新"""
                self.events[event.event_id] = event

            @override
            def list_events(
                self, start_date: date, end_date: date, location_id: str
            ) -> list[CalendarEvent]:
                """イベントのリストを取得"""
                return [
                    event
                    for event in self.events.values()
                    if event.location_id == location_id and start_date <= event.date <= end_date
                ]

        # Mock実装をインスタンス化
        repository = MockCalendarRepository()

        # テストデータ
        event1 = CalendarEvent(
            event_id="event_001",
            title="潮汐 東京湾 (大潮)",
            description="[TIDE]\n- 満潮: 06:12 (162cm)",
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        event2 = CalendarEvent(
            event_id="event_002",
            title="潮汐 東京湾 (中潮)",
            description="[TIDE]\n- 満潮: 07:30 (150cm)",
            date=date(2026, 2, 9),
            location_id="tokyo_bay",
        )

        # upsert_event のテスト
        repository.upsert_event(event1)
        repository.upsert_event(event2)

        # get_event のテスト
        retrieved_event = repository.get_event("event_001")
        assert retrieved_event is not None
        assert retrieved_event.event_id == "event_001"
        assert retrieved_event.title == "潮汐 東京湾 (大潮)"

        # 存在しないイベントの取得
        non_existent = repository.get_event("event_999")
        assert non_existent is None

        # list_events のテスト
        events = repository.list_events(
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 9),
            location_id="tokyo_bay",
        )
        assert len(events) == 2
        assert events[0].event_id in ("event_001", "event_002")
        assert events[1].event_id in ("event_001", "event_002")

        # 範囲外のイベントは取得されない
        events = repository.list_events(
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 11),
            location_id="tokyo_bay",
        )
        assert len(events) == 0

        # 異なる地点のイベントは取得されない
        events = repository.list_events(
            start_date=date(2026, 2, 8),
            end_date=date(2026, 2, 9),
            location_id="sagami_bay",
        )
        assert len(events) == 0

    def test_upsert_idempotency(self) -> None:
        """upsert_event の冪等性を確認"""

        class MockCalendarRepository(ICalendarRepository):
            """テスト用のMock実装"""

            def __init__(self) -> None:
                self.events: dict[str, CalendarEvent] = {}

            @override
            def get_event(self, event_id: str) -> CalendarEvent | None:
                return self.events.get(event_id)

            @override
            def generate_event_id_for_location_date(
                self, location_id: str, target_date: date
            ) -> str:
                return f"{location_id}_{target_date.isoformat()}"

            @override
            def upsert_event(self, event: CalendarEvent) -> None:
                self.events[event.event_id] = event

            @override
            def list_events(
                self, start_date: date, end_date: date, location_id: str
            ) -> list[CalendarEvent]:
                return list(self.events.values())

        repository = MockCalendarRepository()

        # 初回作成
        event = CalendarEvent(
            event_id="event_001",
            title="潮汐 東京湾 (大潮)",
            description="[TIDE]\n- 満潮: 06:12 (162cm)",
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        repository.upsert_event(event)
        assert len(repository.events) == 1

        # 同じIDで再度upsert（更新）
        updated_event = CalendarEvent(
            event_id="event_001",
            title="潮汐 東京湾 (中潮)",  # タイトル変更
            description="[TIDE]\n- 満潮: 07:30 (150cm)",  # 内容変更
            date=date(2026, 2, 8),
            location_id="tokyo_bay",
        )
        repository.upsert_event(updated_event)

        # 件数は増えず、内容が更新される
        assert len(repository.events) == 1
        retrieved = repository.get_event("event_001")
        assert retrieved is not None
        assert retrieved.title == "潮汐 東京湾 (中潮)"
        assert "07:30" in retrieved.description
