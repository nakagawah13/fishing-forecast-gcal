"""SyncTideUseCaseのユニットテスト

このモジュールは SyncTideUseCase の単体テストを提供します。
Mockリポジトリを使用して、外部依存なしにロジックを検証します。
"""

from datetime import UTC, date, datetime
from pathlib import Path
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
        return Location(
            id="tokyo",
            name="東京湾",
            latitude=35.6762,
            longitude=139.6503,
            station_id="TK",
        )

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
            prime_times=[
                (
                    datetime(2026, 2, 10, 4, 12, tzinfo=UTC),
                    datetime(2026, 2, 10, 8, 12, tzinfo=UTC),
                ),
                (
                    datetime(2026, 2, 10, 16, 45, tzinfo=UTC),
                    datetime(2026, 2, 10, 20, 45, tzinfo=UTC),
                ),
            ],
        )

    @pytest.fixture
    def mock_tide_repo(self, tide_data: Tide, target_date: date) -> Mock:
        """Mockの潮汐データリポジトリ"""
        repo = Mock()

        # 複数日分のデータを返す（前後3日分 = 計7日）
        # 対象日のみ実データ、他の日は簡易的な大潮データを返す
        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            if d == target_date:
                return tide_data
            # 他の日は簡易的な大潮データ
            return Tide(
                date=d,
                tide_type=TideType.SPRING,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=160.0,
                        event_type="high",
                    ),
                ],
            )

        repo.get_tide_data.side_effect = get_tide_data_side_effect
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

        # 検証: 潮汐データが複数日分取得されたか（前後3日 + 対象日 = 7日）
        assert mock_tide_repo.get_tide_data.call_count == 7
        # 対象日が呼ばれていることを確認
        calls = mock_tide_repo.get_tide_data.call_args_list
        target_date_calls = [c for c in calls if c[0][1] == target_date]
        assert len(target_date_calls) == 1

        # 検証: 既存イベントが確認されたか（ドメインロジックでevent_id生成）
        expected_event_id = CalendarEvent.generate_event_id(location.id, target_date)
        mock_calendar_repo.get_event.assert_called_once_with(expected_event_id)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: upsert_event に existing=None が渡されたか（新規イベント）
        call_kwargs = mock_calendar_repo.upsert_event.call_args[1]
        assert call_kwargs.get("existing") is None

        # 検証: upsert_event に渡されたイベントの内容
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert event.event_id == expected_event_id
        assert event.title == "🔴東京湾 (大潮)"  # 絵文字付き新形式
        assert event.date == target_date
        assert event.location_id == location.id
        # 絵文字凡例が含まれることを確認
        assert "🔴大潮 🟠中潮 🔵小潮 ⚪長潮 🟢若潮" in event.description
        assert "[TIDE]" in event.description
        assert "[FORECAST]" in event.description
        assert "[NOTES]" in event.description
        assert "06:12 (162cm)" in event.description  # 満潮1
        assert "18:45 (155cm)" in event.description  # 満潮2
        assert "12:34 (58cm)" in event.description  # 干潮
        assert "04:12-08:12" in event.description  # 時合い帯1
        assert "16:45-20:45" in event.description  # 時合い帯2

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
            title="🟠東京湾 (中潮)",  # 既存は中潮
            description="[TIDE]\n古いデータ\n\n[FORECAST]\n古い予報\n\n[NOTES]\nユーザーメモ",
            date=target_date,
            location_id=location.id,
        )
        mock_calendar_repo.get_event.return_value = existing_event

        # 実行
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: upsert_event に existing=existing_event が渡されたか（重複API回避）
        call_kwargs = mock_calendar_repo.upsert_event.call_args[1]
        assert call_kwargs.get("existing") is existing_event

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
            title="🔴東京湾 (大潮)",  # 絵文字付き
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
            prime_times=[
                (
                    datetime(2026, 2, 10, 10, 0, tzinfo=UTC),
                    datetime(2026, 2, 10, 14, 0, tzinfo=UTC),
                ),
            ],
        )

        # side_effectで複数日分のデータを返す
        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            if d == target_date:
                return tide_data
            # 他の日は小潮データ
            return Tide(
                date=d,
                tide_type=TideType.NEAP,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=100.0,
                        event_type="high",
                    ),
                ],
            )

        mock_tide_repo.get_tide_data.side_effect = get_tide_data_side_effect

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
            prime_times=None,
        )

        # side_effectで複数日分のデータを返す
        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            if d == target_date:
                return tide_data
            # 他の日は長潮データ
            return Tide(
                date=d,
                tide_type=TideType.LONG,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=100.0,
                        event_type="high",
                    ),
                ],
            )

        mock_tide_repo.get_tide_data.side_effect = get_tide_data_side_effect

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

    def test_execute_marks_midpoint_day(
        self,
        mock_calendar_repo: Mock,
        location: Location,
    ) -> None:
        """連続期間の中央日にマーカーが付くことを確認"""
        # 大潮が3日連続するデータを準備（2/9-2/11）
        # 中央日は2/10
        target_date = date(2026, 2, 10)

        # Mockリポジトリを手動設定
        mock_tide_repo = Mock()

        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            # 2/9-2/11は大潮、他は中潮
            if date(2026, 2, 9) <= d <= date(2026, 2, 11):
                tide_type = TideType.SPRING
            else:
                tide_type = TideType.MODERATE

            return Tide(
                date=d,
                tide_type=tide_type,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=160.0,
                        event_type="high",
                    ),
                ],
                prime_times=[
                    (
                        datetime(d.year, d.month, d.day, 4, 0, tzinfo=UTC),
                        datetime(d.year, d.month, d.day, 8, 0, tzinfo=UTC),
                    )
                ],
            )

        mock_tide_repo.get_tide_data.side_effect = get_tide_data_side_effect
        mock_calendar_repo.get_event.return_value = None

        # UseCaseを作成して実行
        usecase = SyncTideUseCase(tide_repo=mock_tide_repo, calendar_repo=mock_calendar_repo)
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: イベント本文に中央日マーカーが含まれているか
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert "⭐ 中央日" in event.description
        assert "[TIDE]" in event.description

    def test_execute_no_marker_on_non_midpoint_day(
        self,
        mock_calendar_repo: Mock,
        location: Location,
    ) -> None:
        """非中央日にはマーカーが付かないことを確認"""
        # 大潮が3日連続するが、対象日は開始日（2/9）
        target_date = date(2026, 2, 9)

        # Mockリポジトリを手動設定
        mock_tide_repo = Mock()

        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            # 2/9-2/11は大潮、他は中潮
            if date(2026, 2, 9) <= d <= date(2026, 2, 11):
                tide_type = TideType.SPRING
            else:
                tide_type = TideType.MODERATE

            return Tide(
                date=d,
                tide_type=tide_type,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=160.0,
                        event_type="high",
                    ),
                ],
                prime_times=[
                    (
                        datetime(d.year, d.month, d.day, 4, 0, tzinfo=UTC),
                        datetime(d.year, d.month, d.day, 8, 0, tzinfo=UTC),
                    )
                ],
            )

        mock_tide_repo.get_tide_data.side_effect = get_tide_data_side_effect
        mock_calendar_repo.get_event.return_value = None

        # UseCaseを作成して実行
        usecase = SyncTideUseCase(tide_repo=mock_tide_repo, calendar_repo=mock_calendar_repo)
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: イベント本文に中央日マーカーが含まれていないか
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert "⭐ 中央日" not in event.description
        assert "[TIDE]" in event.description

    def test_execute_no_marker_on_non_spring_tide_midpoint(
        self,
        mock_calendar_repo: Mock,
        location: Location,
    ) -> None:
        """中潮や小潮の中央日にはマーカーが付かないことを確認"""
        # 中潮が3日連続し、対象日は中央日（2/10）だがマーカーは付かない
        target_date = date(2026, 2, 10)

        # Mockリポジトリを手動設定
        mock_tide_repo = Mock()

        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            # 2/9-2/11は中潮、他は小潮
            if date(2026, 2, 9) <= d <= date(2026, 2, 11):
                tide_type = TideType.MODERATE
            else:
                tide_type = TideType.NEAP

            return Tide(
                date=d,
                tide_type=tide_type,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=130.0,
                        event_type="high",
                    ),
                ],
                prime_times=[
                    (
                        datetime(d.year, d.month, d.day, 4, 0, tzinfo=UTC),
                        datetime(d.year, d.month, d.day, 8, 0, tzinfo=UTC),
                    )
                ],
            )

        mock_tide_repo.get_tide_data.side_effect = get_tide_data_side_effect
        mock_calendar_repo.get_event.return_value = None

        # UseCaseを作成して実行
        usecase = SyncTideUseCase(tide_repo=mock_tide_repo, calendar_repo=mock_calendar_repo)
        usecase.execute(location, target_date)

        # 検証: upsert_event が呼ばれたか
        mock_calendar_repo.upsert_event.assert_called_once()

        # 検証: 中潮の中央日だがマーカーが付かないことを確認
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]

        assert "⭐ 中央日" not in event.description
        assert "[TIDE]" in event.description


class TestSyncTideUseCaseTideGraph:
    """タイドグラフ画像の生成・アップロード統合テスト"""

    @pytest.fixture
    def location(self) -> Location:
        """テスト用の地点データ"""
        return Location(
            id="tokyo",
            name="東京湾",
            latitude=35.6762,
            longitude=139.6503,
            station_id="TK",
        )

    @pytest.fixture
    def target_date(self) -> date:
        """テスト用の対象日"""
        return date(2026, 2, 10)

    @pytest.fixture
    def tide_data(self) -> Tide:
        """テスト用の潮汐データ（時合い帯あり）"""
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
            ],
            prime_times=[
                (datetime(2026, 2, 10, 4, 12, tzinfo=UTC), datetime(2026, 2, 10, 8, 12, tzinfo=UTC))
            ],
        )

    @pytest.fixture
    def mock_tide_repo(self, tide_data: Tide, target_date: date) -> Mock:
        """Mockの潮汐データリポジトリ"""
        repo = Mock()

        def get_tide_data_side_effect(location: Location, d: date) -> Tide:
            if d == target_date:
                return tide_data
            return Tide(
                date=d,
                tide_type=TideType.SPRING,
                events=[
                    TideEvent(
                        time=datetime(d.year, d.month, d.day, 6, 0, tzinfo=UTC),
                        height_cm=160.0,
                        event_type="high",
                    ),
                ],
            )

        repo.get_tide_data.side_effect = get_tide_data_side_effect
        repo.get_hourly_heights.return_value = [
            (0.0, 100.0),
            (6.0, 162.0),
            (12.0, 58.0),
            (18.0, 155.0),
            (24.0, 100.0),
        ]
        return repo

    @pytest.fixture
    def mock_calendar_repo(self) -> Mock:
        """Mockのカレンダーリポジトリ"""
        repo = Mock()
        repo.get_event.return_value = None
        return repo

    @pytest.fixture
    def mock_tide_graph_service(self, tmp_path: Path) -> Mock:
        """Mockのタイドグラフサービス"""
        service = Mock()
        image_path = tmp_path / "tide_tokyo_20260210.png"
        image_path.write_bytes(b"fake-png-data")
        service.generate_graph.return_value = image_path
        return service

    @pytest.fixture
    def mock_drive_client(self) -> Mock:
        """MockのGoogleDriveクライアント"""
        client = Mock()
        client.get_or_create_folder.return_value = "folder-id-123"
        client.upload_or_update_file.return_value = {
            "file_id": "file-id-456",
            "file_url": "https://drive.google.com/file/d/file-id-456/view?usp=drivesdk",
        }
        return client

    def test_graph_enabled_generates_and_uploads(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        mock_tide_graph_service: Mock,
        mock_drive_client: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """画像機能有効時、生成→アップロード→attachments付きで登録される"""
        usecase = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_tide_graph_service,
            drive_client=mock_drive_client,
            drive_folder_name="test-folder",
        )

        usecase.execute(location, target_date)

        # タイドグラフが生成された
        mock_tide_graph_service.generate_graph.assert_called_once()
        call_kwargs = mock_tide_graph_service.generate_graph.call_args[1]
        assert call_kwargs["target_date"] == target_date
        assert call_kwargs["location_name"] == "東京湾"
        assert call_kwargs["location_id"] == "tokyo"
        assert call_kwargs["tide_type"] == TideType.SPRING
        assert call_kwargs["prime_times"] is not None

        # hourly_heights が取得された
        mock_tide_repo.get_hourly_heights.assert_called_once_with(location, target_date)

        # Drive にアップロードされた（冪等アップロード）
        mock_drive_client.get_or_create_folder.assert_called_once_with("test-folder")
        mock_drive_client.upload_or_update_file.assert_called_once()

        # upsert_event に attachments が渡された
        call_kwargs = mock_calendar_repo.upsert_event.call_args[1]
        attachments = call_kwargs.get("attachments")
        assert attachments is not None
        assert len(attachments) == 1
        assert attachments[0]["mimeType"] == "image/png"
        assert "drive.google.com" in attachments[0]["fileUrl"]

    def test_graph_disabled_no_attachment(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """画像機能無効時（デフォルト）、attachments なしで登録される"""
        usecase = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
        )

        usecase.execute(location, target_date)

        # タイドグラフ関連は呼ばれない
        mock_tide_repo.get_hourly_heights.assert_not_called()

        # upsert_event に attachments=None が渡された
        call_kwargs = mock_calendar_repo.upsert_event.call_args[1]
        assert call_kwargs.get("attachments") is None

    def test_graph_generation_failure_continues_without_attachment(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        mock_drive_client: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """画像生成が失敗しても、attachments なしでイベント登録は継続される"""
        mock_graph_service = Mock()
        mock_graph_service.generate_graph.side_effect = RuntimeError("Font not found")

        usecase = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_graph_service,
            drive_client=mock_drive_client,
        )

        usecase.execute(location, target_date)

        # upsert_event は呼ばれている（attachments なし）
        mock_calendar_repo.upsert_event.assert_called_once()
        call_kwargs = mock_calendar_repo.upsert_event.call_args[1]
        assert call_kwargs.get("attachments") is None

    def test_drive_upload_failure_continues_without_attachment(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        mock_tide_graph_service: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """Driveアップロードが失敗しても、attachments なしでイベント登録は継続される"""
        mock_drive = Mock()
        mock_drive.get_or_create_folder.return_value = "folder-id"
        mock_drive.upload_or_update_file.side_effect = RuntimeError("Network error")

        usecase = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_tide_graph_service,
            drive_client=mock_drive,
        )

        usecase.execute(location, target_date)

        # upsert_event は呼ばれている（attachments なし）
        mock_calendar_repo.upsert_event.assert_called_once()
        call_kwargs = mock_calendar_repo.upsert_event.call_args[1]
        assert call_kwargs.get("attachments") is None

    def test_notes_preserved_with_graph_attachment(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        mock_tide_graph_service: Mock,
        mock_drive_client: Mock,
        location: Location,
        target_date: date,
    ) -> None:
        """既存 NOTES と画像添付が同時に正しく処理される"""
        expected_event_id = CalendarEvent.generate_event_id(location.id, target_date)
        existing_event = CalendarEvent(
            event_id=expected_event_id,
            title="🔴東京湾 (大潮)",
            description="[TIDE]\n古いデータ\n\n[FORECAST]\n\n[NOTES]\nユーザーメモ",
            date=target_date,
            location_id=location.id,
        )
        mock_calendar_repo.get_event.return_value = existing_event

        usecase = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_tide_graph_service,
            drive_client=mock_drive_client,
        )

        usecase.execute(location, target_date)

        # NOTES が保持されている
        call_args = mock_calendar_repo.upsert_event.call_args
        event: CalendarEvent = call_args[0][0]
        assert "ユーザーメモ" in event.description

        # attachments も渡されている
        call_kwargs = call_args[1]
        assert call_kwargs.get("attachments") is not None
        assert len(call_kwargs["attachments"]) == 1

    def test_temp_file_cleaned_up_after_upload(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        mock_drive_client: Mock,
        location: Location,
        target_date: date,
        tmp_path: Path,
    ) -> None:
        """アップロード後に一時ファイルが削除される"""
        image_path = tmp_path / "tide_tokyo_20260210.png"
        image_path.write_bytes(b"fake-png-data")

        mock_graph_service = Mock()
        mock_graph_service.generate_graph.return_value = image_path

        usecase = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_graph_service,
            drive_client=mock_drive_client,
        )

        usecase.execute(location, target_date)

        # 一時ファイルが削除されている
        assert not image_path.exists()

    def test_tide_graph_enabled_property(
        self,
        mock_tide_repo: Mock,
        mock_calendar_repo: Mock,
        mock_tide_graph_service: Mock,
        mock_drive_client: Mock,
    ) -> None:
        """_tide_graph_enabled プロパティが両方注入時のみ True を返す"""
        # 両方あり → True
        uc_both = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_tide_graph_service,
            drive_client=mock_drive_client,
        )
        assert uc_both._tide_graph_enabled is True

        # graph_service のみ → False
        uc_graph_only = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            tide_graph_service=mock_tide_graph_service,
        )
        assert uc_graph_only._tide_graph_enabled is False

        # drive_client のみ → False
        uc_drive_only = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
            drive_client=mock_drive_client,
        )
        assert uc_drive_only._tide_graph_enabled is False

        # 両方なし → False
        uc_none = SyncTideUseCase(
            tide_repo=mock_tide_repo,
            calendar_repo=mock_calendar_repo,
        )
        assert uc_none._tide_graph_enabled is False
