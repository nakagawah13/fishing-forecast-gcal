"""cleanup-images command implementation.

Google Drive上の古いタイドグラフ画像を削除するコマンドです。
"""

import argparse
import logging
import sys
from typing import TYPE_CHECKING, Any

from fishing_forecast_gcal.application.usecases.cleanup_drive_images_usecase import (
    CleanupDriveImagesUseCase,
)
from fishing_forecast_gcal.infrastructure.clients.google_drive_client import (
    GoogleDriveClient,
)
from fishing_forecast_gcal.presentation.commands.common import add_common_arguments

if TYPE_CHECKING:
    from fishing_forecast_gcal.presentation.config_loader import AppConfig

logger = logging.getLogger(__name__)


def add_arguments(subparsers: Any) -> None:
    """Add cleanup-images subcommand and its arguments.

    cleanup-images サブコマンドと引数を定義します。

    Args:
        subparsers: Subparsers action to add the command to.
    """
    parser = subparsers.add_parser(
        "cleanup-images",
        help="Delete old tide graph images from Google Drive",
    )
    add_common_arguments(parser)

    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain images (default: 30)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )


def run(
    args: argparse.Namespace,
    config: "AppConfig",
) -> None:
    """Execute cleanup-images command.

    Google Drive 上の古いタイドグラフ画像を削除します。

    Args:
        args: Parsed CLI arguments.
        config: Application configuration.
    """
    settings = config.settings

    if args.dry_run:
        logger.warning("[DRY-RUN] No files will be deleted")

    # 依存オブジェクトの構築
    logger.info("Initializing dependencies...")

    drive_client = GoogleDriveClient(
        credentials_path=settings.google_credentials_path,
        token_path=settings.google_token_path,
    )
    drive_client.authenticate()
    logger.info("Google Drive authentication successful")

    # UseCase
    cleanup_usecase = CleanupDriveImagesUseCase(drive_client=drive_client)

    folder_name = config.tide_graph.drive_folder_name
    retention_days = args.retention_days

    logger.info("Folder: %s", folder_name)
    logger.info("Retention: %d days", retention_days)

    # メイン処理
    result = cleanup_usecase.execute(
        folder_name=folder_name,
        retention_days=retention_days,
        dry_run=args.dry_run,
    )

    # 結果サマリー
    logger.info("=" * 70)
    if args.dry_run:
        logger.info("Cleanup dry-run completed")
        logger.info("  Total files: %d", result.total_found)
        logger.info("  Would delete: %d file(s)", result.total_expired)
    else:
        logger.info("Cleanup completed")
        logger.info("  Total files: %d", result.total_found)
        logger.info("  Expired: %d", result.total_expired)
        logger.info("  Deleted: %d", result.total_deleted)
        logger.info("  Failed: %d", result.total_failed)
    logger.info("=" * 70)

    if result.total_failed > 0:
        sys.exit(1)
