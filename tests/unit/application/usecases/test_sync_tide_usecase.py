"""SyncTideUseCaseのユニットテスト

このモジュールは SyncTideUseCase の単体テストを提供します。
Mockリポジトリを使用して、外部依存なしにロジックを検証します。
"""

from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest

from fishing_forecast_gcal.application.usecases.sync_tide_usecase import SyncTideUseCase
from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide, TideEvent, TideType


class TestSyncTideUseCase:
    """SyncTideUseCaseのテストクラス"""

    @pytest.fixture
    def location(self) -> Location:
        """テスト用の地点データ"""
        return Location(id="tokyo", name="東京湾", latitude=35.6762, longitude=139.6503)

    @pytest.fixture
    def target_date(self) -> date:
        """テスト用の対象日"""
        return date(2026, 2, 10)

    @pytest.fixture
    def tide_data(self) -> Tide:
        """テスト用の潮汐データ"""
        return Tide(
            date=date(2026, 2, 10),
            tide_type=TideType.SPRING,
            events=[
                TideEvent(
                    time=datetime(2026, 2, 10, 6, 12, tzinfo=UTC),
                    height_cm=162.0,
                    event_type="high",
                ),
                TideEvent(
                    time=datetime(2026, 2, 10, 12, 34, tzinfo=UTC),
                    height_cm=58.0,
                    event_type="low",
                ),
                TideEvent(
                    time=datetime(2026, 2, 10, 18, 45, tzinfo=UTC),
                    height_cm=155.0,
                    event_type="high",
                ),
            ],
            prime_time_start=datetime(2026, 2, 10, 4, 12, tzinfo=UTC),
            prime_time_end=datetime(2026, 2, 10, 8, 12, tzinfo=UTC),
        )

    @pytest.fixture
    def mock_tide_repo(self, tide_data: Tide) -> Mock:
        """Mockの潮汐データリポジトリ"""
        repo = Mock()
        repo.get_tide_data.return_value = tide_data
        return repo

    @pytest.fixture
    def mock_calendar_repo(self) -> Mock:
        """Mockのカレンダーリポジトリ"""
        repo = Mock()
        repo.get_event.return_value = None  # 既存イベントなし
        return repo

    @pytest.fixture
    def usecase(self, mock_tide_repo: Mock, mock_calendar_repo: Mock) -> SyncTideUseCase:
        """テスト対象のユースケース"""
        return SyncTideUseCase(tide_repo=mock_tide_repo, calendar_repo=mock_calendar_repo)

    def test_execute_creates_new_event(
        self,
        usecase: SyncTideUseCase,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """新規イベントが作成されることを確認"""
        # 実行
        usecase.execute(location, target_date)

        # 検証: 潮汐データが取得されたか
        mock_tide_repo.get_tide_data.assert_called_once_with(location, target_date)

        # 検証: 既存イベントが確認されたか（ドメインロジックでevent_id生成）
        expected_event_id = CalendarEvent.generate_event_id(location.id, target_date)
        mock_calendar_repo.get_event.assert_called_once_with(expected_event_id)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: upsert_event に渡されたイベントの内容
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert event.event_id == expected_event_id
        assert event.title == "潮汐 東京湾 (大潮)"
        assert event.date == target_date
        assert event.location_id == location.id
        assert "[TIDE]" in event.description
        assert "[FORECAST]" in event.description
        assert "[NOTES]" in event.description
        assert "06:12 (162cm)" in event.description  # 満潮1
        assert "18:45 (155cm)" in event.description  # 満潮2
        assert "12:34 (58cm)" in event.description  # 干潮
        assert "04:12-08:12" in event.description  # 時合い帯

    def test_execute_updates_existing_event(
        self,
        usecase: SyncTideUseCase,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """既存イベントが更新されることを確認"""
        # 既存イベントを設定
        expected_event_id = CalendarEvent.generate_event_id(location.id, target_date)
        existing_event = CalendarEvent(
            event_id=expected_event_id,
            title="潮汐 東京湾 (中潮)",
            description="[TIDE]\n古いデータ\n\n[FORECAST]\n古い予報\n\n[NOTES]\nユーザーメモ",
            date=target_date,
            location_id=location.id,
        )
        mock_calendar_repo.get_event.return_value = existing_event

        # 実行
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: 既存の[NOTES]が保持されているか
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert "ユーザーメモ" in event.description
        assert "[NOTES]" in event.description

    def test_execute_preserves_notes_section(
        self,
        usecase: SyncTideUseCase,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """[NOTES]セクションが保持されることを確認"""
        # 既存イベントに[NOTES]セクションを含める
        expected_event_id = CalendarEvent.generate_event_id(location.id, target_date)
        existing_event = CalendarEvent(
            event_id=expected_event_id,
            title="潮汐 東京湾 (大潮)",
            description="[TIDE]\n- 満潮: 06:00\n\n[FORECAST]\n風速: 5m/s\n\n[NOTES]\n手動で追加したメモ",
            date=target_date,
            location_id=location.id,
        )
        mock_calendar_repo.get_event.return_value = existing_event

        # 実行
        usecase.execute(location, target_date)

        # 検証: [NOTES]が保持されているか
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert "手動で追加したメモ" in event.description

    def test_execute_with_single_high_tide(
        self,
        usecase: SyncTideUseCase,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """満潮が1回のみの場合に正しく処理されることを確認"""
        # 満潮1回、干潮2回のデータ
        tide_data = Tide(
            date=target_date,
            tide_type=TideType.NEAP,
            events=[
                TideEvent(
                    time=datetime(2026, 2, 10, 0, 30, tzinfo=UTC),
                    height_cm=50.0,
                    event_type="low",
                ),
                TideEvent(
                    time=datetime(2026, 2, 10, 12, 0, tzinfo=UTC),
                    height_cm=120.0,
                    event_type="high",
                ),
                TideEvent(
                    time=datetime(2026, 2, 10, 23, 30, tzinfo=UTC),
                    height_cm=55.0,
                    event_type="low",
                ),
            ],
            prime_time_start=datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
            prime_time_end=datetime(2026, 2, 10, 14, 0, tzinfo=UTC),
        )
        mock_tide_repo.get_tide_data.return_value = tide_data

        # 実行
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: 本文に満潮1回、干潮2回が記載されているか
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert "12:00 (120cm)" in event.description  # 満潮
        assert "00:30 (50cm)" in event.description  # 干潮1
        assert "23:30 (55cm)" in event.description  # 干潮2

    def test_execute_with_no_prime_time(
        self,
        usecase: SyncTideUseCase,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """時合い帯がない場合に正しく処理されることを確認"""
        # 時合い帯なしのデータ
        tide_data = Tide(
            date=target_date,
            tide_type=TideType.LONG,
            events=[
                TideEvent(
                    time=datetime(2026, 2, 10, 6, 0, tzinfo=UTC),
                    height_cm=100.0,
                    event_type="low",
                ),
                TideEvent(
                    time=datetime(2026, 2, 10, 18, 0, tzinfo=UTC),
                    height_cm=120.0,
                    event_type="high",
                ),
            ],
            prime_time_start=None,
            prime_time_end=None,
        )
        mock_tide_repo.get_tide_data.return_value = tide_data

        # 実行
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: 本文に時合い帯が含まれていないか
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        # 時合い帯の行が含まれていないことを確認
        assert "時合い:" not in event.description

    def test_execute_raises_on_tide_data_error(
        self,
        usecase: SyncTideUseCase,
        mock_tide_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """潮汐データ取得失敗時に例外が発生することを確認"""
        # 潮汐データ取得でエラーを発生させる
        mock_tide_repo.get_tide_data.side_effect = RuntimeError("Tide data fetch failed")

        # 実行 & 検証
        with pytest.raises(RuntimeError) as exc_info:
            usecase.execute(location, target_date)

        assert "Failed to sync tide" in str(exc_info.value)

    def test_execute_raises_on_calendar_error(
        self,
        usecase: SyncTideUseCase,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """カレンダー更新失敗時に例外が発生することを確認"""
        # upsert_event でエラーを発生させる
        mock_calendar_repo.upsert_event.side_effect = RuntimeError("Calendar update failed")

        # 実行 & 検証
        with pytest.raises(RuntimeError) as exc_info:
            usecase.execute(location, target_date)

        assert "Failed to sync tide" in str(exc_info.value)
