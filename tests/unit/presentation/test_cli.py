"""CLI エントリーポイントの単体テスト"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

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
