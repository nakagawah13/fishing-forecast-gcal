"""Tests for common CLI utilities.

共通ユーティリティ（setup_logging, parse_date, add_common_arguments, add_period_arguments）のテスト。
"""

import argparse
from datetime import date
from unittest.mock import Mock, patch

import pytest

from fishing_forecast_gcal.presentation.commands.common import (
    add_common_arguments,
    add_period_arguments,
    parse_date,
    setup_logging,
)


class TestSetupLogging:
    """setup_logging function tests."""

    @patch("fishing_forecast_gcal.presentation.commands.common.logging.basicConfig")
    def test_setup_logging_non_verbose(self, mock_basic_config: Mock) -> None:
        """Standard log level initialization."""
        setup_logging(verbose=False)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == 20  # logging.INFO

    @patch("fishing_forecast_gcal.presentation.commands.common.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_basic_config: Mock) -> None:
        """Verbose log level initialization."""
        setup_logging(verbose=True)

        mock_basic_config.assert_called_once()
        call_kwargs = mock_basic_config.call_args[1]
        assert call_kwargs["level"] == 10  # logging.DEBUG


class TestParseDate:
    """parse_date function tests."""

    def test_parse_date_valid(self) -> None:
        """Valid date format."""
        result = parse_date("2026-02-08")
        assert result == date(2026, 2, 8)

    def test_parse_date_invalid_format(self) -> None:
        """Invalid date format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("2026/02/08")

    def test_parse_date_invalid_date(self) -> None:
        """Non-existent date."""
        with pytest.raises(ValueError):
            parse_date("2026-02-30")


class TestAddCommonArguments:
    """add_common_arguments function tests."""

    def test_adds_config_and_verbose(self) -> None:
        """Adds --config and --verbose arguments."""
        parser = argparse.ArgumentParser()
        add_common_arguments(parser)

        args = parser.parse_args([])
        assert args.config == "config/config.yaml"
        assert args.verbose is False

    def test_config_custom_value(self) -> None:
        """Custom --config value."""
        parser = argparse.ArgumentParser()
        add_common_arguments(parser)

        args = parser.parse_args(["--config", "custom.yaml"])
        assert args.config == "custom.yaml"

    def test_verbose_flag(self) -> None:
        """--verbose flag is set."""
        parser = argparse.ArgumentParser()
        add_common_arguments(parser)

        args = parser.parse_args(["--verbose"])
        assert args.verbose is True


class TestAddPeriodArguments:
    """add_period_arguments function tests."""

    def test_adds_period_arguments_defaults(self) -> None:
        """Adds period arguments with defaults."""
        parser = argparse.ArgumentParser()
        add_period_arguments(parser)

        args = parser.parse_args([])
        assert args.location_id is None
        assert args.start_date is None
        assert args.end_date is None
        assert args.days is None
        assert args.dry_run is False

    def test_location_id(self) -> None:
        """--location-id argument."""
        parser = argparse.ArgumentParser()
        add_period_arguments(parser)

        args = parser.parse_args(["--location-id", "tk"])
        assert args.location_id == "tk"

    def test_days_as_int(self) -> None:
        """--days argument parsed as integer."""
        parser = argparse.ArgumentParser()
        add_period_arguments(parser)

        args = parser.parse_args(["--days", "30"])
        assert args.days == 30
