#!/usr/bin/env python3
"""Fetch JMA tide prediction text data.

This script downloads JMA tide prediction (suisan) text files.
For parsing logic, see tests.support.jma_suisan_parser module.

気象庁の潮位表(推算)テキストをダウンロードします。
パースロジックは tests.support.jma_suisan_parser モジュールを参照してください。

Usage:
    uv run python scripts/fetch_jma_suisan_tide_data.py --station TK --year 2026

Data Source:
    https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/index.php
    Format:
    https://www.data.jma.go.jp/kaiyou/db/tide/suisan/readme.html
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx が必要です: uv add httpx", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

JMA_SUISAN_URL_TEMPLATE = (
    "https://www.data.jma.go.jp/kaiyou/data/db/tide/suisan/txt/{year}/{station}.txt"
)


def fetch_suisan_text(station_id: str, year: int) -> str:
    """Fetch JMA suisan text for the given station and year.

    Args:
        station_id (str): JMA station code (e.g. "TK").
                          (地点記号)
        year (int): Target year.
                    (対象年)

    Returns:
        str: Raw text content.
             (生テキスト)
    """
    url = JMA_SUISAN_URL_TEMPLATE.format(year=year, station=station_id)
    logger.info("ダウンロード中: %s", url)
    with httpx.Client(follow_redirects=True) as client:
        response = client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.text


def main() -> int:
    """Run CLI for fetching JMA suisan text.

    気象庁の推算テキストを取得してファイル保存します。

    Returns:
        int: Exit code.
    """
    parser = argparse.ArgumentParser(description="Fetch JMA suisan tide data")
    parser.add_argument("--station", required=True, help="JMA station code (e.g. TK)")
    parser.add_argument("--year", required=True, type=int, help="Target year")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output file path (default: ./jma_suisan_{station}_{year}.txt)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

    output_path = args.output or Path(f"jma_suisan_{args.station}_{args.year}.txt")
    text = fetch_suisan_text(args.station, args.year)
    output_path.write_text(text, encoding="utf-8")

    logger.info("保存完了: %s", output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
