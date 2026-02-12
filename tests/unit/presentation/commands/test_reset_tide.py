"""Tests for reset-tide command module.

reset-tide コマンドの引数定義と実行ロジックのテスト。
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from fishing_forecast_gcal.application.usecases.reset_tide_usecase import ResetResult
from fishing_forecast_gcal.presentation.commands import reset_tide


class TestResetTideAddArguments:
    """reset_tide.add_arguments tests."""

    def test_adds_reset_tide_subcommand(self) -> None:
        """reset-tide subcommand is registered."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        reset_tide.add_arguments(subparsers)

        args = parser.parse_args(["reset-tide"])
        assert args.command == "reset-tide"

    def test_reset_tide_has_force_argument(self) -> None:
        """reset-tide has --force argument."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        reset_tide.add_arguments(subparsers)

        args = parser.parse_args(["reset-tide", "--force"])
        assert args.force is True

    def test_reset_tide_force_short_option(self) -> None:
        """--force short option -f works."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        reset_tide.add_arguments(subparsers)

        args = parser.parse_args(["reset-tide", "-f"])
        assert args.force is True


class TestResetTideRun:
    """reset_tide.run tests."""

    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.ResetTideUseCase")
    def test_run_basic_flow_with_force(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Basic flow with --force (skips confirmation)."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.force = True

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=5, total_deleted=5, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        reset_tide.run(
            mock_args,
            mock_settings,
            [mock_location],
            date(2026, 3, 1),
            date(2026, 3, 3),
        )

        mock_calendar_client.authenticate.assert_called_once()
        mock_usecase.execute.assert_called_once()
        call_kwargs = mock_usecase.execute.call_args
        assert call_kwargs[1]["dry_run"] is False

    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.ResetTideUseCase")
    def test_run_dry_run(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Dry-run mode passes dry_run=True."""
        mock_args = Mock()
        mock_args.dry_run = True
        mock_args.force = True

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=3, total_deleted=0, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        reset_tide.run(
            mock_args,
            mock_settings,
            [mock_location],
            date(2026, 3, 1),
            date(2026, 3, 3),
        )

        call_kwargs = mock_usecase.execute.call_args
        assert call_kwargs[1]["dry_run"] is True

    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.ResetTideUseCase")
    def test_run_with_failures_exits_1(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Exits with code 1 when delete failures occur."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.force = True

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=5, total_deleted=3, total_failed=2
        )
        mock_usecase_class.return_value = mock_usecase

        with pytest.raises(SystemExit) as exc_info:
            reset_tide.run(
                mock_args,
                mock_settings,
                [mock_location],
                date(2026, 3, 1),
                date(2026, 3, 3),
            )

        assert exc_info.value.code == 1

    @patch("builtins.input", return_value="n")
    def test_run_confirmation_declined(self, mock_input: Mock) -> None:
        """Exits when user declines confirmation."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.force = False

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()

        with pytest.raises(SystemExit) as exc_info:
            reset_tide.run(
                mock_args,
                mock_settings,
                [mock_location],
                date(2026, 3, 1),
                date(2026, 3, 3),
            )

        assert exc_info.value.code == 0

    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.ResetTideUseCase")
    @patch("builtins.input", return_value="y")
    def test_run_confirmation_accepted(
        self,
        mock_input: Mock,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Executes when user accepts confirmation."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.force = False

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=2, total_deleted=2, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        reset_tide.run(
            mock_args,
            mock_settings,
            [mock_location],
            date(2026, 3, 1),
            date(2026, 3, 3),
        )

        mock_usecase.execute.assert_called_once()

    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.GoogleCalendarClient")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.CalendarRepository")
    @patch("fishing_forecast_gcal.presentation.commands.reset_tide.ResetTideUseCase")
    def test_run_dry_run_skips_confirmation(
        self,
        mock_usecase_class: Mock,
        mock_calendar_repo_class: Mock,
        mock_calendar_client_class: Mock,
    ) -> None:
        """Dry-run mode skips confirmation prompt."""
        mock_args = Mock()
        mock_args.dry_run = True
        mock_args.force = False

        mock_location = Mock()
        mock_location.id = "test_loc"
        mock_location.name = "Test Location"

        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"
        mock_settings.calendar_id = "test-cal-id"

        mock_calendar_client = Mock()
        mock_calendar_client_class.return_value = mock_calendar_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = ResetResult(
            total_found=3, total_deleted=0, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        # input is not mocked — if called, it would raise
        reset_tide.run(
            mock_args,
            mock_settings,
            [mock_location],
            date(2026, 3, 1),
            date(2026, 3, 3),
        )

        mock_usecase.execute.assert_called_once()
