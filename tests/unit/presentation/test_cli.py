"""CLI dispatcher (main, parse_args) tests.

cli.py が薄いディスパッチャーとして正しく機能することを検証します。
引数パース、設定読み込み、コマンド委譲のテストです。
各コマンドの実行ロジックは commands/ 配下のテストで検証します。
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from fishing_forecast_gcal.presentation.cli import (
    _resolve_locations,
    _resolve_period,
    main,
    parse_args,
    parse_date,
    setup_logging,
)


class TestReExports:
    """Backward-compatible re-exports from cli module."""

    def test_setup_logging_is_exported(self) -> None:
        """setup_logging is re-exported from commands.common."""
        assert callable(setup_logging)

    def test_parse_date_is_exported(self) -> None:
        """parse_date is re-exported from commands.common."""
        result = parse_date("2026-02-08")
        assert result == date(2026, 2, 8)


class TestParseArgs:
    """parse_args function tests."""

    def test_parse_args_sync_tide_minimal(self) -> None:
        """sync-tide subcommand minimal arguments."""
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
        """sync-tide subcommand all options."""
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
        """--days option."""
        with patch("sys.argv", ["prog", "sync-tide", "--days", "30"]):
            args = parse_args()

        assert args.days == 30
        assert args.end_date is None

    def test_parse_args_sync_tide_days_short_option(self) -> None:
        """--days short form -d."""
        with patch("sys.argv", ["prog", "sync-tide", "-d", "7"]):
            args = parse_args()

        assert args.days == 7

    def test_parse_args_days_and_end_date_mutually_exclusive(self) -> None:
        """--days and --end-date together raises error."""
        with patch(
            "sys.argv",
            ["prog", "sync-tide", "--days", "7", "--end-date", "2026-03-08"],
        ):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_days_zero_error(self) -> None:
        """--days 0 raises error."""
        with patch("sys.argv", ["prog", "sync-tide", "--days", "0"]):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_days_negative_error(self) -> None:
        """--days negative value raises error."""
        with patch("sys.argv", ["prog", "sync-tide", "--days", "-5"]):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_no_subcommand(self) -> None:
        """No subcommand raises error."""
        with patch("sys.argv", ["prog"]):
            with pytest.raises(SystemExit):
                parse_args()


class TestParseArgsResetTide:
    """reset-tide subcommand argument parsing tests."""

    def test_parse_args_reset_tide_minimal(self) -> None:
        """reset-tide minimal arguments."""
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
        """reset-tide all options."""
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
        """reset-tide --days option."""
        with patch("sys.argv", ["prog", "reset-tide", "--days", "14"]):
            args = parse_args()

        assert args.days == 14
        assert args.end_date is None

    def test_parse_args_reset_tide_force_short_option(self) -> None:
        """--force short form -f."""
        with patch("sys.argv", ["prog", "reset-tide", "-f"]):
            args = parse_args()

        assert args.force is True

    def test_parse_args_reset_tide_days_and_end_date_exclusive(self) -> None:
        """reset-tide --days and --end-date together raises error."""
        with patch(
            "sys.argv",
            ["prog", "reset-tide", "--days", "7", "--end-date", "2026-03-08"],
        ):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_reset_tide_days_negative_error(self) -> None:
        """reset-tide --days negative value raises error."""
        with patch("sys.argv", ["prog", "reset-tide", "--days", "-1"]):
            with pytest.raises(SystemExit):
                parse_args()


class TestParseArgsCleanupImages:
    """cleanup-images subcommand argument parsing tests."""

    def test_parse_args_cleanup_images_minimal(self) -> None:
        """cleanup-images minimal arguments."""
        with patch("sys.argv", ["prog", "cleanup-images"]):
            args = parse_args()

        assert args.command == "cleanup-images"
        assert args.config == "config/config.yaml"
        assert args.retention_days == 30
        assert args.dry_run is False
        assert args.verbose is False

    def test_parse_args_cleanup_images_all_options(self) -> None:
        """cleanup-images all options."""
        with patch(
            "sys.argv",
            [
                "prog",
                "cleanup-images",
                "--config",
                "custom.yaml",
                "--retention-days",
                "7",
                "--dry-run",
                "--verbose",
            ],
        ):
            args = parse_args()

        assert args.command == "cleanup-images"
        assert args.config == "custom.yaml"
        assert args.retention_days == 7
        assert args.dry_run is True
        assert args.verbose is True

    def test_parse_args_cleanup_images_retention_days_zero_error(self) -> None:
        """--retention-days 0 raises error."""
        with patch("sys.argv", ["prog", "cleanup-images", "--retention-days", "0"]):
            with pytest.raises(SystemExit):
                parse_args()

    def test_parse_args_cleanup_images_retention_days_negative_error(self) -> None:
        """--retention-days negative value raises error."""
        with patch("sys.argv", ["prog", "cleanup-images", "--retention-days", "-5"]):
            with pytest.raises(SystemExit):
                parse_args()


class TestResolveLocations:
    """_resolve_locations function tests."""

    def test_returns_all_locations_when_no_filter(self) -> None:
        """Returns all locations when location_id is None."""
        loc1 = Mock()
        loc1.id = "loc_a"
        loc2 = Mock()
        loc2.id = "loc_b"

        result = _resolve_locations([loc1, loc2], None)
        assert result == [loc1, loc2]

    def test_filters_by_location_id(self) -> None:
        """Filters locations by ID."""
        loc1 = Mock()
        loc1.id = "loc_a"
        loc2 = Mock()
        loc2.id = "loc_b"

        result = _resolve_locations([loc1, loc2], "loc_b")
        assert result == [loc2]

    def test_exits_when_location_id_not_found(self) -> None:
        """Exits with code 1 when location ID is not found."""
        loc1 = Mock()
        loc1.id = "loc_a"

        with pytest.raises(SystemExit) as exc_info:
            _resolve_locations([loc1], "nonexistent")

        assert exc_info.value.code == 1


class TestResolvePeriod:
    """_resolve_period function tests."""

    def test_with_end_date(self) -> None:
        """End date from --end-date argument."""
        args = Mock()
        args.start_date = "2026-02-08"
        args.end_date = "2026-02-10"
        args.days = None

        start, end = _resolve_period(args, tide_register_months=1)
        assert start == date(2026, 2, 8)
        assert end == date(2026, 2, 10)

    def test_with_days(self) -> None:
        """End date calculated from --days."""
        args = Mock()
        args.start_date = "2026-02-08"
        args.end_date = None
        args.days = 3

        start, end = _resolve_period(args, tide_register_months=1)
        assert start == date(2026, 2, 8)
        assert end == date(2026, 2, 10)

    def test_with_config_default(self) -> None:
        """End date calculated from config tide_register_months."""
        args = Mock()
        args.start_date = "2026-02-08"
        args.end_date = None
        args.days = None

        start, end = _resolve_period(args, tide_register_months=1)
        assert start == date(2026, 2, 8)
        assert end == date(2026, 3, 10)

    def test_start_after_end_exits(self) -> None:
        """Exits when start date is after end date."""
        args = Mock()
        args.start_date = "2026-03-10"
        args.end_date = "2026-02-08"
        args.days = None

        with pytest.raises(SystemExit) as exc_info:
            _resolve_period(args, tide_register_months=1)

        assert exc_info.value.code == 1


class TestMain:
    """main function integration tests."""

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.run")
    def test_main_dispatches_sync_tide(
        self,
        mock_sync_run: Mock,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """main() dispatches to sync_tide.run."""
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

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_load_config.return_value = mock_config

        main()

        mock_sync_run.assert_called_once()
        call_args = mock_sync_run.call_args
        assert call_args[0][0] == mock_args
        assert call_args[0][1] == mock_config

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.run")
    def test_main_dispatches_cleanup_images(
        self,
        mock_cleanup_run: Mock,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """main() dispatches to cleanup_images.run."""
        mock_args = Mock()
        mock_args.command = "cleanup-images"
        mock_args.config = "config/config.yaml"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        mock_config_path = Mock()
        mock_config_path.exists.return_value = True
        mock_path.return_value = mock_config_path

        mock_settings = Mock()
        mock_settings.timezone = "Asia/Tokyo"
        mock_settings.calendar_id = "test-calendar-id-12345"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_load_config.return_value = mock_config

        main()

        mock_cleanup_run.assert_called_once_with(mock_args, mock_config)

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_config_file_not_found(
        self,
        mock_path: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """Exits when config file is not found."""
        mock_args = Mock()
        mock_args.config = "missing.yaml"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

        mock_config_path = Mock()
        mock_config_path.exists.return_value = False
        mock_path.return_value = mock_config_path

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    def test_main_keyboard_interrupt(
        self,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """Exits with 130 on keyboard interrupt."""
        mock_parse_args.side_effect = KeyboardInterrupt()

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 130

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.run")
    def test_main_days_option_calculates_end_date(
        self,
        mock_sync_run: Mock,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """--days option calculates correct end_date."""
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

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_load_config.return_value = mock_config

        main()

        # Verify end_date is 2026-02-10 (3 days: 8, 9, 10)
        call_args = mock_sync_run.call_args[0]
        assert call_args[3] == date(2026, 2, 8)  # start_date
        assert call_args[4] == date(2026, 2, 10)  # end_date

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    def test_main_location_id_not_found(
        self,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """Exits when specified location ID is not found."""
        mock_args = Mock()
        mock_args.command = "sync-tide"
        mock_args.config = "config/config.yaml"
        mock_args.location_id = "nonexistent"
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

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

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.cli.parse_args")
    @patch("fishing_forecast_gcal.presentation.cli.common.setup_logging")
    @patch("fishing_forecast_gcal.presentation.cli.load_config")
    @patch("fishing_forecast_gcal.presentation.cli.Path")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.run")
    def test_main_dispatches_reset_tide(
        self,
        mock_reset_run: Mock,
        mock_path: Mock,
        mock_load_config: Mock,
        mock_setup_logging: Mock,
        mock_parse_args: Mock,
    ) -> None:
        """main() dispatches to reset_tide.run."""
        mock_args = Mock()
        mock_args.command = "reset-tide"
        mock_args.config = "config/config.yaml"
        mock_args.location_id = None
        mock_args.start_date = "2026-03-01"
        mock_args.end_date = "2026-03-03"
        mock_args.days = None
        mock_args.dry_run = False
        mock_args.verbose = False
        mock_parse_args.return_value = mock_args

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

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.locations = [mock_location]
        mock_load_config.return_value = mock_config

        main()

        mock_reset_run.assert_called_once()
        call_args = mock_reset_run.call_args[0]
        assert call_args[0] == mock_args
        assert call_args[1] == mock_settings
