"""CLI entry point for fishing-forecast-gcal.

このモジュールはコマンドライン引数のパース、依存オブジェクトの構築、
UseCaseの呼び出しを統合します。
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from fishing_forecast_gcal.application.usecases.reset_tide_usecase import ResetTideUseCase
from fishing_forecast_gcal.application.usecases.sync_tide_usecase import SyncTideUseCase
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
)
from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from fishing_forecast_gcal.infrastructure.repositories.calendar_repository import (
    CalendarRepository,
)
from fishing_forecast_gcal.infrastructure.repositories.tide_data_repository import (
    TideDataRepository,
)
from fishing_forecast_gcal.presentation.config_loader import load_config

if TYPE_CHECKING:
    from fishing_forecast_gcal.domain.models.location import Location
    from fishing_forecast_gcal.presentation.config_loader import AppSettings

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """ロギング設定を初期化

    Args:
        verbose: 詳細ログを出力する場合True
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    """コマンドライン引数をパース

    Returns:
        パースされた引数
    """
    parser = argparse.ArgumentParser(
        prog="fishing-forecast-gcal",
        description="Fishing forecast calendar integration tool",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync-tide サブコマンド
    sync_tide_parser = subparsers.add_parser(
        "sync-tide",
        help="Sync tide data to Google Calendar",
    )

    sync_tide_parser.add_argument(
        "--config",
        "-c",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )

    sync_tide_parser.add_argument(
        "--location-id",
        "-l",
        help="Target location ID (if omitted, process all locations in config)",
    )

    sync_tide_parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format (default: today)",
    )

    sync_tide_parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format (default: based on config)",
    )

    sync_tide_parser.add_argument(
        "--days",
        "-d",
        type=int,
        help="Number of days to sync from start date (mutually exclusive with --end-date)",
    )

    sync_tide_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually creating events",
    )

    sync_tide_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # reset-tide サブコマンド
    reset_tide_parser = subparsers.add_parser(
        "reset-tide",
        help="Delete tide events from Google Calendar",
    )

    reset_tide_parser.add_argument(
        "--config",
        "-c",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )

    reset_tide_parser.add_argument(
        "--location-id",
        "-l",
        help="Target location ID (if omitted, process all locations in config)",
    )

    reset_tide_parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format (default: today)",
    )

    reset_tide_parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format (default: based on config)",
    )

    reset_tide_parser.add_argument(
        "--days",
        "-d",
        type=int,
        help="Number of days from start date (mutually exclusive with --end-date)",
    )

    reset_tide_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    reset_tide_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )

    reset_tide_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parsed = parser.parse_args()

    # --days と --end-date の排他チェック
    if (
        parsed.command in ("sync-tide", "reset-tide")
        and parsed.days is not None
        and parsed.end_date is not None
    ):
        parser.error("--days and --end-date are mutually exclusive")

    # --days の値バリデーション
    if (
        parsed.command in ("sync-tide", "reset-tide")
        and parsed.days is not None
        and parsed.days < 1
    ):
        parser.error("--days must be a positive integer (>= 1)")

    return parsed


def parse_date(date_str: str) -> date:
    """日付文字列をパース

    Args:
        date_str: YYYY-MM-DD形式の日付文字列

    Returns:
        dateオブジェクト

    Raises:
        ValueError: 日付フォーマットが不正な場合
    """
    try:
        return date.fromisoformat(date_str)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD") from e


def main() -> None:
    """Main entry point. (メインエントリーポイント)"""
    try:
        args = parse_args()
        setup_logging(args.verbose)

        command_label = "Tide sync" if args.command == "sync-tide" else "Tide reset"
        logger.info("=" * 70)
        logger.info("fishing-forecast-gcal - %s", command_label)
        logger.info("=" * 70)

        # 設定ファイル読み込み
        logger.info("Loading configuration from: %s", args.config)
        config_path = Path(args.config)

        if not config_path.exists():
            logger.error("Configuration file not found: %s", config_path)
            logger.error("Please create config/config.yaml from config/config.yaml.template")
            sys.exit(1)

        config = load_config(str(config_path))
        settings = config.settings
        logger.info("Configuration loaded successfully")
        logger.info("  Timezone: %s", settings.timezone)
        logger.info("  Calendar ID: %s", settings.calendar_id[:30] + "...")

        # 対象地点の決定
        if args.location_id:
            # 指定された地点IDを検証
            target_locations = [loc for loc in config.locations if loc.id == args.location_id]
            if not target_locations:
                logger.error("Location ID not found in config: %s", args.location_id)
                logger.error(
                    "Available locations: %s",
                    ", ".join(loc.id for loc in config.locations),
                )
                sys.exit(1)
        else:
            target_locations = config.locations

        logger.info(
            "Target locations: %s",
            ", ".join(f"{loc.name} ({loc.id})" for loc in target_locations),
        )

        # 対象期間の決定
        start_date = parse_date(args.start_date) if args.start_date else date.today()

        if args.end_date:
            end_date = parse_date(args.end_date)
        elif args.days is not None:
            end_date = start_date + timedelta(days=args.days - 1)
        else:
            # 設定ファイルの tide_register_months に基づいて計算
            months = settings.tide_register_months
            end_date = start_date + timedelta(days=30 * months)

        if start_date > end_date:
            logger.error("Start date must be before end date")
            sys.exit(1)

        total_days = (end_date - start_date).days + 1
        logger.info("Target period: %s to %s (%d days)", start_date, end_date, total_days)

        # コマンド別処理
        if args.command == "sync-tide":
            _run_sync_tide(args, settings, target_locations, start_date, end_date)
        elif args.command == "reset-tide":
            _run_reset_tide(args, settings, target_locations, start_date, end_date)

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        sys.exit(1)


def _run_sync_tide(
    args: argparse.Namespace,
    settings: "AppSettings",
    target_locations: list["Location"],
    start_date: date,
    end_date: date,
) -> None:
    """Execute sync-tide command.

    潮汐データをGoogle Calendarに同期します。

    Args:
        args: Parsed CLI arguments
        settings: Application settings
        target_locations: List of target locations
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
    """
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

    # UseCase
    sync_usecase = SyncTideUseCase(
        tide_repo=tide_repo,
        calendar_repo=calendar_repo,
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


def _run_reset_tide(
    args: argparse.Namespace,
    settings: "AppSettings",
    target_locations: list["Location"],
    start_date: date,
    end_date: date,
) -> None:
    """Execute reset-tide command.

    指定期間・地点の潮汐イベントを削除します。

    Args:
        args: Parsed CLI arguments
        settings: Application settings
        target_locations: List of target locations
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
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


if __name__ == "__main__":
    main()
