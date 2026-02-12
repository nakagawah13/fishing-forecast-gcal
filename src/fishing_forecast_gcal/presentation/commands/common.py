"""Common utilities shared across CLI commands.

共通ユーティリティ（ロギング設定、日付パース、共通引数）を提供します。
"""

import argparse
import logging
from datetime import date


def setup_logging(verbose: bool = False) -> None:
    """Initialize logging configuration.

    ロギング設定を初期化します。

    Args:
        verbose: If True, set log level to DEBUG. (詳細ログを出力する場合True)
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_date(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format.

    日付文字列をパースします。

    Args:
        date_str: Date string in YYYY-MM-DD format.

    Returns:
        Parsed date object.

    Raises:
        ValueError: If the date format is invalid.
    """
    try:
        return date.fromisoformat(date_str)
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD") from e


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common arguments shared across commands.

    全コマンド共通の引数（--config, --verbose）を追加します。

    Args:
        parser: Argument parser to add arguments to.
    """
    parser.add_argument(
        "--config",
        "-c",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )


def add_period_arguments(parser: argparse.ArgumentParser) -> None:
    """Add period-related arguments (--location-id, --start-date, --end-date, --days).

    期間関連の共通引数を追加します。sync-tide / reset-tide で共通使用。

    Args:
        parser: Argument parser to add arguments to.
    """
    parser.add_argument(
        "--location-id",
        "-l",
        help="Target location ID (if omitted, process all locations in config)",
    )

    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format (default: today)",
    )

    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format (default: based on config)",
    )

    parser.add_argument(
        "--days",
        "-d",
        type=int,
        help="Number of days to sync from start date (mutually exclusive with --end-date)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually making changes",
    )
