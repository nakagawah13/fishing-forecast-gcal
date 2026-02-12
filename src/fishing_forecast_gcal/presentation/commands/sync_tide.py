"""sync-tide command implementation.

潮汐データをGoogle Calendarに同期するコマンドです。
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fishing_forecast_gcal.application.usecases.sync_tide_usecase import SyncTideUseCase
from fishing_forecast_gcal.domain.services.tide_graph_service import TideGraphService
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
)
from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from fishing_forecast_gcal.infrastructure.clients.google_drive_client import (
    GoogleDriveClient,
)
from fishing_forecast_gcal.infrastructure.repositories.calendar_repository import (
    CalendarRepository,
)
from fishing_forecast_gcal.infrastructure.repositories.tide_data_repository import (
    TideDataRepository,
)
from fishing_forecast_gcal.presentation.commands.common import (
    add_common_arguments,
    add_period_arguments,
)

if TYPE_CHECKING:
    from fishing_forecast_gcal.domain.models.location import Location
    from fishing_forecast_gcal.presentation.config_loader import AppConfig

logger = logging.getLogger(__name__)


def add_arguments(subparsers: Any) -> None:
    """Add sync-tide subcommand and its arguments.

    sync-tide サブコマンドと引数を定義します。

    Args:
        subparsers: Subparsers action to add the command to.
    """
    parser = subparsers.add_parser(
        "sync-tide",
        help="Sync tide data to Google Calendar",
    )
    add_common_arguments(parser)
    add_period_arguments(parser)


def run(
    args: argparse.Namespace,
    config: "AppConfig",
    target_locations: list["Location"],
    start_date: date,
    end_date: date,
) -> None:
    """Execute sync-tide command.

    潮汐データをGoogle Calendarに同期します。

    Args:
        args: Parsed CLI arguments.
        config: Application configuration.
        target_locations: List of target locations.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
    """
    settings = config.settings
    if args.dry_run:
        logger.warning("[DRY-RUN] No events will be created")

    # 依存オブジェクトの構築
    logger.info("Initializing dependencies...")

    # Google Calendar クライアント
    calendar_client = GoogleCalendarClient(
        credentials_path=settings.google_credentials_path,
        token_path=settings.google_token_path,
    )
    calendar_client.authenticate()
    logger.info("Google Calendar authentication successful")

    # リポジトリ
    harmonics_dir = Path("config/harmonics")
    tide_adapter = TideCalculationAdapter(harmonics_dir)
    tide_repo = TideDataRepository(tide_adapter)
    calendar_repo = CalendarRepository(
        client=calendar_client,
        calendar_id=settings.calendar_id,
    )

    # タイドグラフ関連の依存（有効な場合のみ構築）
    tide_graph_service: TideGraphService | None = None
    drive_client: GoogleDriveClient | None = None
    drive_folder_name: str = "fishing-forecast-tide-graphs"

    if config.tide_graph.enabled:
        logger.info("Tide graph attachment is enabled")
        tide_graph_service = TideGraphService()

        drive_client = GoogleDriveClient(
            credentials_path=settings.google_credentials_path,
            token_path=settings.google_token_path,
        )
        drive_client.authenticate()
        logger.info("Google Drive authentication successful")

        drive_folder_name = config.tide_graph.drive_folder_name

    # UseCase
    sync_usecase = SyncTideUseCase(
        tide_repo=tide_repo,
        calendar_repo=calendar_repo,
        tide_graph_service=tide_graph_service,
        drive_client=drive_client,
        drive_folder_name=drive_folder_name,
    )

    # メイン処理
    logger.info("Starting sync process...")
    total_processed = 0
    total_errors = 0

    for location in target_locations:
        logger.info("Processing location: %s (%s)", location.name, location.id)

        current_date = start_date
        while current_date <= end_date:
            try:
                if args.dry_run:
                    logger.info("[DRY-RUN] Would sync: %s", current_date)
                else:
                    sync_usecase.execute(location, current_date)
                    logger.debug("Synced: %s", current_date)

                total_processed += 1

            except Exception as e:
                logger.error("Failed to sync %s: %s", current_date, e)
                total_errors += 1

            current_date += timedelta(days=1)

    # 結果サマリー
    logger.info("=" * 70)
    logger.info("Sync completed")
    logger.info("  Processed: %d days", total_processed)
    logger.info("  Errors: %d", total_errors)
    logger.info("=" * 70)

    if total_errors > 0:
        sys.exit(1)
