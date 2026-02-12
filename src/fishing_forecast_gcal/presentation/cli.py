"""CLI entry point for fishing-forecast-gcal.

薄いディスパッチャーとして機能し、引数パース・設定読み込み・コマンド委譲を行います。
各コマンドの実装は presentation.commands 配下のモジュールに委譲します。
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from fishing_forecast_gcal.presentation.commands import common
from fishing_forecast_gcal.presentation.commands.common import parse_date, setup_logging
from fishing_forecast_gcal.presentation.config_loader import load_config

if TYPE_CHECKING:
    from fishing_forecast_gcal.domain.models.location import Location

logger = logging.getLogger(__name__)

# Re-export for backward compatibility and test patching
__all__ = ["main", "parse_args", "parse_date", "setup_logging"]


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    コマンドライン引数をパースします。

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="fishing-forecast-gcal",
        description="Fishing forecast calendar integration tool",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # 各コマンドの引数定義を委譲
    from fishing_forecast_gcal.presentation.commands import (
        cleanup_images,
        reset_tide,
        sync_tide,
    )

    sync_tide.add_arguments(subparsers)
    reset_tide.add_arguments(subparsers)
    cleanup_images.add_arguments(subparsers)

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

    # --retention-days の値バリデーション
    if (
        parsed.command == "cleanup-images"
        and parsed.retention_days is not None
        and parsed.retention_days < 1
    ):
        parser.error("--retention-days must be a positive integer (>= 1)")

    return parsed


def _resolve_locations(
    config_locations: list["Location"],
    location_id: str | None,
) -> list["Location"]:
    """Resolve target locations from config and CLI argument.

    対象地点を決定します。

    Args:
        config_locations: All locations from config file.
        location_id: Optional location ID filter from CLI.

    Returns:
        List of target locations.
    """
    if location_id:
        target_locations = [loc for loc in config_locations if loc.id == location_id]
        if not target_locations:
            logger.error("Location ID not found in config: %s", location_id)
            logger.error(
                "Available locations: %s",
                ", ".join(loc.id for loc in config_locations),
            )
            sys.exit(1)
        return target_locations
    return config_locations


def _resolve_period(
    args: argparse.Namespace,
    tide_register_months: int,
) -> tuple[date, date]:
    """Resolve target period from CLI arguments and config.

    対象期間を決定します。

    Args:
        args: Parsed CLI arguments with start_date, end_date, days.
        tide_register_months: Default months from config.

    Returns:
        Tuple of (start_date, end_date).
    """
    start_date = parse_date(args.start_date) if args.start_date else date.today()

    if args.end_date:
        end_date = parse_date(args.end_date)
    elif args.days is not None:
        end_date = start_date + timedelta(days=args.days - 1)
    else:
        end_date = start_date + timedelta(days=30 * tide_register_months)

    if start_date > end_date:
        logger.error("Start date must be before end date")
        sys.exit(1)

    return start_date, end_date


def main() -> None:
    """Main entry point. (メインエントリーポイント)"""
    try:
        args = parse_args()
        common.setup_logging(args.verbose)

        command_labels = {
            "sync-tide": "Tide sync",
            "reset-tide": "Tide reset",
            "cleanup-images": "Drive image cleanup",
        }
        command_label = command_labels.get(args.command, args.command)
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

        # cleanup-images は地点・期間不要なので専用ルートに
        if args.command == "cleanup-images":
            from fishing_forecast_gcal.presentation.commands.cleanup_images import (
                run as run_cleanup,
            )

            run_cleanup(args, config)
            return

        # 対象地点の決定
        target_locations = _resolve_locations(config.locations, args.location_id)
        logger.info(
            "Target locations: %s",
            ", ".join(f"{loc.name} ({loc.id})" for loc in target_locations),
        )

        # 対象期間の決定
        start_date, end_date = _resolve_period(args, settings.tide_register_months)
        total_days = (end_date - start_date).days + 1
        logger.info("Target period: %s to %s (%d days)", start_date, end_date, total_days)

        # コマンド別処理
        if args.command == "sync-tide":
            from fishing_forecast_gcal.presentation.commands.sync_tide import (
                run as run_sync,
            )

            run_sync(args, config, target_locations, start_date, end_date)
        elif args.command == "reset-tide":
            from fishing_forecast_gcal.presentation.commands.reset_tide import (
                run as run_reset,
            )

            run_reset(args, settings, target_locations, start_date, end_date)

    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
