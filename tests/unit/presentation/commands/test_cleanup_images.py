"""Tests for cleanup-images command module.

cleanup-images コマンドの引数定義と実行ロジックのテスト。
"""

from unittest.mock import Mock, patch

import pytest

from fishing_forecast_gcal.application.usecases.cleanup_drive_images_usecase import (
    CleanupResult,
)
from fishing_forecast_gcal.presentation.commands import cleanup_images


class TestCleanupImagesAddArguments:
    """cleanup_images.add_arguments tests."""

    def test_adds_cleanup_images_subcommand(self) -> None:
        """cleanup-images subcommand is registered."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        cleanup_images.add_arguments(subparsers)

        args = parser.parse_args(["cleanup-images"])
        assert args.command == "cleanup-images"

    def test_cleanup_images_has_retention_days(self) -> None:
        """cleanup-images has --retention-days argument."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        cleanup_images.add_arguments(subparsers)

        args = parser.parse_args(["cleanup-images", "--retention-days", "7"])
        assert args.retention_days == 7

    def test_cleanup_images_retention_days_default(self) -> None:
        """--retention-days defaults to 30."""
        import argparse

        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        cleanup_images.add_arguments(subparsers)

        args = parser.parse_args(["cleanup-images"])
        assert args.retention_days == 30


class TestCleanupImagesRun:
    """cleanup_images.run tests."""

    def _create_mock_config(self) -> Mock:
        """Create mock config for cleanup-images.

        Mock設定オブジェクトを生成します。

        Returns:
            Mock config object.
        """
        mock_settings = Mock()
        mock_settings.google_credentials_path = "creds.json"
        mock_settings.google_token_path = "token.json"

        mock_tide_graph = Mock()
        mock_tide_graph.drive_folder_name = "fishing-forecast-tide-graphs"

        mock_config = Mock()
        mock_config.settings = mock_settings
        mock_config.tide_graph = mock_tide_graph

        return mock_config

    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.GoogleDriveClient")
    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.CleanupDriveImagesUseCase")
    def test_run_basic_flow(
        self,
        mock_usecase_class: Mock,
        mock_drive_client_class: Mock,
    ) -> None:
        """Basic flow: builds dependencies and executes."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.retention_days = 30

        mock_config = self._create_mock_config()

        mock_drive_client = Mock()
        mock_drive_client_class.return_value = mock_drive_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = CleanupResult(
            total_found=5, total_expired=2, total_deleted=2, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        cleanup_images.run(mock_args, mock_config)

        mock_drive_client.authenticate.assert_called_once()
        mock_usecase.execute.assert_called_once_with(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
            dry_run=False,
        )

    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.GoogleDriveClient")
    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.CleanupDriveImagesUseCase")
    def test_run_dry_run(
        self,
        mock_usecase_class: Mock,
        mock_drive_client_class: Mock,
    ) -> None:
        """Dry-run mode passes dry_run=True."""
        mock_args = Mock()
        mock_args.dry_run = True
        mock_args.retention_days = 30

        mock_config = self._create_mock_config()

        mock_drive_client = Mock()
        mock_drive_client_class.return_value = mock_drive_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = CleanupResult(
            total_found=3, total_expired=1, total_deleted=0, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        cleanup_images.run(mock_args, mock_config)

        mock_usecase.execute.assert_called_once_with(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
            dry_run=True,
        )

    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.GoogleDriveClient")
    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.CleanupDriveImagesUseCase")
    def test_run_with_failures_exits_1(
        self,
        mock_usecase_class: Mock,
        mock_drive_client_class: Mock,
    ) -> None:
        """Exits with code 1 when delete failures occur."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.retention_days = 30

        mock_config = self._create_mock_config()

        mock_drive_client = Mock()
        mock_drive_client_class.return_value = mock_drive_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = CleanupResult(
            total_found=3, total_expired=2, total_deleted=1, total_failed=1
        )
        mock_usecase_class.return_value = mock_usecase

        with pytest.raises(SystemExit) as exc_info:
            cleanup_images.run(mock_args, mock_config)

        assert exc_info.value.code == 1

    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.GoogleDriveClient")
    @patch("fishing_forecast_gcal.presentation.commands.cleanup_images.CleanupDriveImagesUseCase")
    def test_run_custom_retention(
        self,
        mock_usecase_class: Mock,
        mock_drive_client_class: Mock,
    ) -> None:
        """Custom retention-days is passed to use case."""
        mock_args = Mock()
        mock_args.dry_run = False
        mock_args.retention_days = 7

        mock_config = self._create_mock_config()

        mock_drive_client = Mock()
        mock_drive_client_class.return_value = mock_drive_client

        mock_usecase = Mock()
        mock_usecase.execute.return_value = CleanupResult(
            total_found=0, total_expired=0, total_deleted=0, total_failed=0
        )
        mock_usecase_class.return_value = mock_usecase

        cleanup_images.run(mock_args, mock_config)

        mock_usecase.execute.assert_called_once_with(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=7,
            dry_run=False,
        )
