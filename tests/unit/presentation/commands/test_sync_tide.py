"""Tests for sync-tide command module.

sync-tide コマンドの引数定義と実行ロジックのテスト。
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from fishing_forecast_gcal.presentation.commands import sync_tide


class TestSyncTideAddArguments:
    """sync_tide.add_arguments tests."""

    def test_adds_sync_tide_subcommand(self) -> None:
        """sync-tide subcommand is registered."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        sync_tide.add_arguments(subparsers)

        args = parser.parse_args(["sync-tide"])
        assert args.command == "sync-tide"

    def test_sync_tide_has_common_arguments(self) -> None:
        """sync-tide has --config and --verbose."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        sync_tide.add_arguments(subparsers)

        args = parser.parse_args(["sync-tide", "--config", "custom.yaml", "--verbose"])
        assert args.config == "custom.yaml"
        assert args.verbose is True

    def test_sync_tide_has_period_arguments(self) -> None:
        """sync-tide has period-related arguments."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        sync_tide.add_arguments(subparsers)

        args = parser.parse_args(
            [
                "sync-tide",
                "--location-id",
                "tk",
                "--start-date",
                "2026-02-08",
                "--end-date",
                "2026-03-08",
                "--days",
                "30",
                "--dry-run",
            ]
        )
        assert args.location_id == "tk"
        assert args.start_date == "2026-02-08"
        assert args.end_date == "2026-03-08"
        assert args.days == 30
        assert args.dry_run is True


class TestSyncTideRun:
    """sync_tide.run tests."""

    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.SyncTideUseCase")
    def test_run_basic_flow(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Basic flow: builds dependencies and executes for each date."""
        mock_args = Mock()
        mock_args.dry_run = False

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.tide_graph.enabled = False

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase_class.return_value = mock_usecase

        sync_tide.run(
            mock_args,
            mock_config,
            [mock_location],
            date(2026, 2, 8),
            date(2026, 2, 9),
        )

        mock_calendar_client.authenticate.assert_called_once()
        assert mock_usecase.execute.call_count == 2

    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.SyncTideUseCase")
    def test_run_dry_run_skips_execute(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Dry-run mode does not call usecase.execute."""
        mock_args = Mock()
        mock_args.dry_run = True

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.tide_graph.enabled = False

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase_class.return_value = mock_usecase

        sync_tide.run(
            mock_args,
            mock_config,
            [mock_location],
            date(2026, 2, 8),
            date(2026, 2, 8),
        )

        mock_usecase.execute.assert_not_called()

    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.SyncTideUseCase")
    def test_run_with_errors_exits_1(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Exits with code 1 when sync errors occur."""
        mock_args = Mock()
        mock_args.dry_run = False

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.tide_graph.enabled = False

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.side_effect = RuntimeError("API error")
        mock_usecase_class.return_value = mock_usecase

        with pytest.raises(SystemExit) as exc_info:
            sync_tide.run(
                mock_args,
                mock_config,
                [mock_location],
                date(2026, 2, 8),
                date(2026, 2, 8),
            )

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.GoogleDriveClient")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideGraphRenderer")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideCalculationAdapter")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.TideDataRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.sync_tide.SyncTideUseCase")
    def test_run_with_tide_graph_enabled(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_tide_repo_class: Mock,
        mock_tide_adapter_class: Mock,
        mock_calendar_client_class: Mock,
        mock_tide_graph_class: Mock,
        mock_drive_client_class: Mock,
    ) -> None:
        """Tide graph dependencies are built when enabled."""
        mock_args = Mock()
        mock_args.dry_run = False

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.tide_graph.enabled = True
        mock_config.tide_graph.drive_folder_name = "tide-graphs"

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_drive_client = Mock()
        mock_drive_client_class.return_value = mock_drive_client

        mock_usecase = Mock()
        mock_usecase_class.return_value = mock_usecase

        sync_tide.run(
            mock_args,
            mock_config,
            [mock_location],
            date(2026, 2, 8),
            date(2026, 2, 8),
        )

        mock_drive_client.authenticate.assert_called_once()
        mock_tide_graph_class.assert_called_once()
        mock_usecase.execute.assert_called_once()
