"""CLI エントリーポイントの単体テスト"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from fishing_forecast_gcal.application.usecases.reset_tide_usecase import ResetResult
from fishing_forecast_gcal.presentation.cli import (
    main,
    parse_args,
    parse_date,
    setup_logging,
)


class TestSetupLogging:
    """setup_logging 関数のテスト"""

    @patch("fishing_forecast_gcal.presentation.cli.logging.basicConfig")
    def test_setup_logging_non_verbose(self, mock_basic_config: Mock) -> None:
        """標準ログレベルでの初期化"""
        setup_logging(verbose=False)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == 20  # logging.INFO

    @patch("fishing_forecast_gcal.presentation.cli.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_basic_config: Mock) -> None:
        """詳細ログレベルでの初期化"""
        setup_logging(verbose=True)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == 10  # logging.DEBUG


class TestParseArgs:
    """parse_args 関数のテスト"""

    def test_parse_args_sync_tide_minimal(self) -> None:
        """sync-tide サブコマンドの最小限の引数"""
        with patch("sys.argv", ["prog", "sync-tide"]):
            args = parse_args()

        assert args.command == "sync-tide"
        assert args.config == "config/config.yaml"
        assert args.location_id is None
        assert args.start_date is None
        assert args.end_date is None
        assert args.days is None
        assert args.dry_run is False
        assert args.verbose is False

    def test_parse_args_sync_tide_all_options(self) -> None:
        """sync-tide サブコマンドのすべてのオプション指定"""
        with patch(
            "sys.argv",
            [
                "prog",
                "sync-tide",
                "--config",
                "custom.yaml",
                "--location-id",
                "test_loc",
                "--start-date",
                "2026-02-08",
                "--end-date",
                "2026-03-08",
                "--dry-run",
                "--verbose",
            ],
        ):
            args = parse_args()

        assert args.command == "sync-tide"
        assert args.config == "custom.yaml"
        assert args.location_id == "test_loc"
        assert args.start_date == "2026-02-08"
        assert args.end_date == "2026-03-08"
        assert args.dry_run is True
        assert args.verbose is True

    def test_parse_args_sync_tide_days_option(self) -> None:
        """--days オプションの指定"""
        with patch("sys.argv", ["prog", "sync-tide", "--days", "30"]):
            args = parse_args()

        assert args.days == 30
        assert args.end_date is None

    def test_parse_args_sync_tide_days_short_option(self) -> None:
        """--days の短縮形 -d の指定"""
        with patch("sys.argv", ["prog", "sync-tide", "-d", "7"]):
            args = parse_args()

        assert args.days == 7

    def test_parse_args_days_and_end_date_mutually_exclusive(self) -> None:
        """--days と --end-date の同時指定でエラー"""
        with patch(
            "sys.argv",
            ["prog", "sync-tide", "--days", "7", "--end-date", "2026-03-08"],
        ):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_days_zero_error(self) -> None:
        """--days 0 でエラー"""
        with patch("sys.argv", ["prog", "sync-tide", "--days", "0"]):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_days_negative_error(self) -> None:
        """--days に負の値でエラー"""
        with patch("sys.argv", ["prog", "sync-tide", "--days", "-5"]):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_no_subcommand(self) -> None:
        """サブコマンドなしでエラー"""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit):
                parse_args()


class TestParseDate:
    """parse_date 関数のテスト"""

    def test_parse_date_valid(self) -> None:
        """正常な日付フォーマット"""
        result = parse_date("2026-02-08")
        assert result == date(2026, 2, 8)

    def test_parse_date_invalid_format(self) -> None:
        """不正な日付フォーマット"""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("2026/02/08")

    def test_parse_date_invalid_date(self) -> None:
        """存在しない日付"""
        with pytest.raises(ValueError):
            parse_date("2026-02-30")


class TestMain:
    """main 関数の統合テスト"""

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.cli.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.SyncTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_basic_flow(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """基本的な処理フロー"""
        # 引数の設定
        mock_args = Mock()
        mock_args.command = "sync-tide"
        mock_args.config = "config/config.yaml"
        mock_args.location_id = None
        mock_args.start_date = "2026-02-08"
        mock_args.end_date = "2026-02-09"
        mock_args.days = None
        mock_args.dry_run = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # 設定ファイルのMock
        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.timezone = "Asia/Tokyo"
        mock_settings.calendar_id = "test-calendar-id-12345"
        mock_settings.tide_register_months = 1
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_config.tide_graph.enabled = False
        mock_load_config.return_value = mock_config

        # クライアント・リポジトリのMock
        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_tide_repo = Mock()
        mock_tide_repo_class.return_value = mock_tide_repo

        mock_calendar_repo = Mock()
        mock_calendar_repo_class.return_value = mock_calendar_repo

        mock_usecase = Mock()
        mock_usecase_class.return_value = mock_usecase

        # 実行
        main()

        # 検証
        mock_setup_logging.assert_called_once_with(False)
        mock_load_config.assert_called_once()
        mock_calendar_client.authenticate.assert_called_once()
        # 2日分の処理（2026-02-08, 2026-02-09）
        assert mock_usecase.execute.call_count == 2

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_config_file_not_found(
        self,
        mock_path: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """設定ファイルが見つからない場合"""
        # 引数の設定
        mock_args = Mock()
        mock_args.config = "missing.yaml"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # 設定ファイルが存在しない
        mock_config_path = Mock()
        mock_config_path.exists.return_value = False
        mock_path.return_value = mock_config_path

        # 実行
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_location_id_not_found(
        self,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """指定された地点IDが存在しない場合"""
        # 引数の設定
        mock_args = Mock()
        mock_args.config = "config/config.yaml"
        mock_args.location_id = "nonexistent"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # 設定ファイルのMock
        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_location = Mock()
        mock_location.id = "existing_loc"

        mock_settings = Mock()
        mock_settings.timezone = "Asia/Tokyo"
        mock_settings.calendar_id = "test-id"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_load_config.return_value = mock_config

        # 実行
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.cli.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.SyncTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_dry_run_mode(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """dry-runモードの動作確認"""
        # 引数の設定（dry-runあり）
        mock_args = Mock()
        mock_args.command = "sync-tide"
        mock_args.config = "config/config.yaml"
        mock_args.location_id = None
        mock_args.start_date = "2026-02-08"
        mock_args.end_date = "2026-02-08"
        mock_args.days = None
        mock_args.dry_run = True
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # 設定ファイルのMock
        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.timezone = "Asia/Tokyo"
        mock_settings.calendar_id = "test-id"
        mock_settings.tide_register_months = 1
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_config.tide_graph.enabled = False
        mock_load_config.return_value = mock_config

        # クライアント・リポジトリのMock
        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase_class.return_value = mock_usecase

        # 実行
        main()

        # dry-runモードではUseCaseが呼び出されない
        mock_usecase.execute.assert_not_called()

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    def test_main_keyboard_interrupt(
        self,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """ユーザー中断時の処理"""
        mock_parse_args.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 130

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.cli.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.SyncTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_days_option_calculates_end_date(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """--days オプションから end_date が正しく算出されること"""
        # 引数の設定（--days=3, start_date=2026-02-08 → 2/8, 2/9, 2/10 の3日間）
        mock_args = Mock()
        mock_args.command = "sync-tide"
        mock_args.config = "config/config.yaml"
        mock_args.location_id = None
        mock_args.start_date = "2026-02-08"
        mock_args.end_date = None
        mock_args.days = 3
        mock_args.dry_run = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        # 設定ファイルのMock
        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.timezone = "Asia/Tokyo"
        mock_settings.calendar_id = "test-calendar-id-12345"
        mock_settings.tide_register_months = 1
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_config.tide_graph.enabled = False
        mock_load_config.return_value = mock_config

        # クライアント・リポジトリのMock
        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_tide_repo = Mock()
        mock_tide_repo_class.return_value = mock_tide_repo

        mock_calendar_repo = Mock()
        mock_calendar_repo_class.return_value = mock_calendar_repo

        mock_usecase = Mock()
        mock_usecase_class.return_value = mock_usecase

        # 実行
        main()

        # 検証: 3日分（2026-02-08, 2026-02-09, 2026-02-10）
        assert mock_usecase.execute.call_count == 3


class TestParseArgsResetTide:
    """reset-tide サブコマンドの引数解析テスト"""

    def test_parse_args_reset_tide_minimal(self) -> None:
        """reset-tide サブコマンドの最小限の引数"""
        with patch("sys.argv", ["prog", "reset-tide"]):
            args = parse_args()

        assert args.command == "reset-tide"
        assert args.config == "config/config.yaml"
        assert args.location_id is None
        assert args.start_date is None
        assert args.end_date is None
        assert args.days is None
        assert args.dry_run is False
        assert args.force is False
        assert args.verbose is False

    def test_parse_args_reset_tide_all_options(self) -> None:
        """reset-tide サブコマンドのすべてのオプション指定"""
        with patch(
            "sys.argv",
            [
                "prog",
                "reset-tide",
                "--config",
                "custom.yaml",
                "--location-id",
                "loc_01",
                "--start-date",
                "2026-03-01",
                "--end-date",
                "2026-03-31",
                "--dry-run",
                "--force",
                "--verbose",
            ],
        ):
            args = parse_args()

        assert args.command == "reset-tide"
        assert args.config == "custom.yaml"
        assert args.location_id == "loc_01"
        assert args.start_date == "2026-03-01"
        assert args.end_date == "2026-03-31"
        assert args.dry_run is True
        assert args.force is True
        assert args.verbose is True

    def test_parse_args_reset_tide_days_option(self) -> None:
        """reset-tide での --days オプション指定"""
        with patch("sys.argv", ["prog", "reset-tide", "--days", "14"]):
            args = parse_args()

        assert args.days == 14
        assert args.end_date is None

    def test_parse_args_reset_tide_force_short_option(self) -> None:
        """--force の短縮形 -f の指定"""
        with patch("sys.argv", ["prog", "reset-tide", "-f"]):
            args = parse_args()

        assert args.force is True

    def test_parse_args_reset_tide_days_and_end_date_exclusive(self) -> None:
        """reset-tide での --days と --end-date の同時指定でエラー"""
        with patch(
            "sys.argv",
            ["prog", "reset-tide", "--days", "7", "--end-date", "2026-03-08"],
        ):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_reset_tide_days_negative_error(self) -> None:
        """reset-tide での --days に負の値でエラー"""
        with patch("sys.argv", ["prog", "reset-tide", "--days", "-1"]):
            with pytest.raises(SystemExit):
                parse_args()


class TestMainResetTide:
    """main 関数の reset-tide コマンドテスト"""

    def _create_mock_args(
        self,
        *,
        start_date: str = "2026-03-01",
        end_date: str = "2026-03-03",
        days: int | None = None,
        dry_run: bool = False,
        force: bool = True,
        location_id: str | None = None,
    ) -> Mock:
        """Create mock args for reset-tide command.

        reset-tide コマンド用のMock引数を生成します。
        """
        mock_args = Mock()
        mock_args.command = "reset-tide"
        mock_args.config = "config/config.yaml"
        mock_args.location_id = location_id
        mock_args.start_date = start_date
        mock_args.end_date = end_date
        mock_args.days = days
        mock_args.dry_run = dry_run
        mock_args.force = force
        mock_args.verbose = False
        return mock_args

    def _create_mock_config(self) -> tuple[Mock, Mock, Mock]:
        """Create mock config, settings, and location.

        Mock設定オブジェクトの一式を生成します。

        Returns:
            Tuple of (config, settings, location) mocks.
        """
        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.timezone = "Asia/Tokyo"
        mock_settings.calendar_id = "test-calendar-id-12345"
        mock_settings.tide_register_months = 1
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]

        return mock_config, mock_settings, mock_location

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.ResetTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_reset_tide_basic_flow(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """reset-tide の基本フロー（--force 指定）"""
        mock_parse_args.return_value = self._create_mock_args(force=True)

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_config, _, _ = self._create_mock_config()
        mock_load_config.return_value = mock_config

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=5, total_deleted=5, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        # 実行
        main()

        # 検証
        mock_setup_logging.assert_called_once_with(False)
        mock_calendar_client.authenticate.assert_called_once()
        mock_usecase.execute.assert_called_once()

        # execute 呼び出しの引数を検証
        call_kwargs = mock_usecase.execute.call_args
        assert call_kwargs[1]["dry_run"] is False

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.ResetTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_reset_tide_dry_run(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """reset-tide の dry-run モード"""
        mock_parse_args.return_value = self._create_mock_args(dry_run=True)

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_config, _, _ = self._create_mock_config()
        mock_load_config.return_value = mock_config

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=3, total_deleted=0, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        # 実行
        main()

        # dry_run=True で呼ばれることを検証
        call_kwargs = mock_usecase.execute.call_args
        assert call_kwargs[1]["dry_run"] is True

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.ResetTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_reset_tide_partial_failure_exits_with_1(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """reset-tide で削除失敗があった場合に exit(1)"""
        mock_parse_args.return_value = self._create_mock_args(force=True)

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_config, _, _ = self._create_mock_config()
        mock_load_config.return_value = mock_config

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=5, total_deleted=3, total_failed=2
        )
        mock_usecase_class.return_value = mock_usecase

        # 実行
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    @patch("builtins.input", return_value="n")
    def test_main_reset_tide_confirmation_declined(
        self,
        mock_input: Mock,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """確認プロンプトで拒否した場合に exit(0)"""
        mock_parse_args.return_value = self._create_mock_args(force=False, dry_run=False)

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_config, _, _ = self._create_mock_config()
        mock_load_config.return_value = mock_config

        # 実行
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.ResetTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    @patch("builtins.input", return_value="y")
    def test_main_reset_tide_confirmation_accepted(
        self,
        mock_input: Mock,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """確認プロンプトで承認した場合に実行される"""
        mock_parse_args.return_value = self._create_mock_args(force=False, dry_run=False)

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_config, _, _ = self._create_mock_config()
        mock_load_config.return_value = mock_config

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=2, total_deleted=2, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        # 実行
        main()

        # UseCase が実行されたことを検証
        mock_usecase.execute.assert_called_once()

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.cli.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.cli.ResetTideUseCase")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_reset_tide_dry_run_skips_confirmation(
        self,
        mock_path: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """dry-run モードでは確認プロンプトをスキップ"""
        mock_parse_args.return_value = self._create_mock_args(dry_run=True, force=False)

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_config, _, _ = self._create_mock_config()
        mock_load_config.return_value = mock_config

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=3, total_deleted=0, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        # 実行（input がモックされていないので、呼ばれたらエラーになる）
        main()

        # UseCase が実行されたことを検証
        mock_usecase.execute.assert_called_once()
