"""reset-tide command implementation.

指定期間・地点の潮汐イベントを削除するコマンドです。
"""

import argparse
import logging
import sys
from datetime import date
from typing import TYPE_CHECKING, Any

from fishing_forecast_gcal.application.usecases.reset_tide_usecase import ResetTideUseCase
from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from fishing_forecast_gcal.infrastructure.repositories.calendar_repository import (
    CalendarRepository,
)
from fishing_forecast_gcal.presentation.commands.common import (
    add_common_arguments,
    add_period_arguments,
)

if TYPE_CHECKING:
    from fishing_forecast_gcal.domain.models.location import Location
    from fishing_forecast_gcal.presentation.config_loader import AppSettings

logger = logging.getLogger(__name__)


def add_arguments(subparsers: Any) -> None:
    """Add reset-tide subcommand and its arguments.

    reset-tide サブコマンドと引数を定義します。

    Args:
        subparsers: Subparsers action to add the command to.
    """
    parser = subparsers.add_parser(
        "reset-tide",
        help="Delete tide events from Google Calendar",
    )
    add_common_arguments(parser)
    add_period_arguments(parser)

    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )


def run(
    args: argparse.Namespace,
    settings: "AppSettings",
    target_locations: list["Location"],
    start_date: date,
    end_date: date,
) -> None:
    """Execute reset-tide command.

    指定期間・地点の潮汐イベントを削除します。

    Args:
        args: Parsed CLI arguments.
        settings: Application settings.
        target_locations: List of target locations.
        start_date: Start date (inclusive).
        end_date: End date (inclusive).
    """
    total_days = (end_date - start_date).days + 1

    # 確認プロンプト（--force なしの場合）
    if not args.dry_run and not args.force:
        location_names = ", ".join(f"{loc.name} ({loc.id})" for loc in target_locations)
        print("\n⚠️  The following tide events will be DELETED:")
        print(f"  Locations: {location_names}")
        print(f"  Period: {start_date} to {end_date} ({total_days} days)")
        print()

        try:
            answer = input("Are you sure? (y/N): ").strip().lower()
        except EOFError:
            answer = ""

        if answer != "y":
            logger.info("Operation cancelled by user")
            sys.exit(0)

    # 依存オブジェクトの構築
    logger.info("Initializing dependencies...")

    calendar_client = GoogleCalendarClient(
        credentials_path=settings.google_credentials_path,
        token_path=settings.google_token_path,
    )
    calendar_client.authenticate()
    logger.info("Google Calendar authentication successful")

    calendar_repo = CalendarRepository(
        client=calendar_client,
        calendar_id=settings.calendar_id,
    )

    # UseCase
    reset_usecase = ResetTideUseCase(calendar_repo=calendar_repo)

    # メイン処理
    logger.info("Starting reset process...")
    grand_total_found = 0
    grand_total_deleted = 0
    grand_total_failed = 0

    for location in target_locations:
        result = reset_usecase.execute(
            location=location,
            start_date=start_date,
            end_date=end_date,
            dry_run=args.dry_run,
        )
        grand_total_found += result.total_found
        grand_total_deleted += result.total_deleted
        grand_total_failed += result.total_failed

    # 結果サマリー
    logger.info("=" * 70)
    if args.dry_run:
        logger.info("Reset dry-run completed")
        logger.info("  Would delete: %d event(s)", grand_total_found)
    else:
        logger.info("Reset completed")
        logger.info("  Found: %d event(s)", grand_total_found)
        logger.info("  Deleted: %d event(s)", grand_total_deleted)
        logger.info("  Failed: %d event(s)", grand_total_failed)
    logger.info("=" * 70)

    if grand_total_failed > 0:
        sys.exit(1)
