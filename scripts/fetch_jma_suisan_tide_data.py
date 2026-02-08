#!/usr/bin/env python3
"""Fetch JMA tide prediction text data.

This script downloads JMA tide prediction (suisan) text files and provides
parsing helpers for daily high/low tide times.

気象庁の潮位表(推算)テキストをダウンロードし、
満潮・干潮の時刻を抽出する補助関数を提供します。

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
from dataclasses import dataclass
from datetime import date, time
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

LINE_LENGTH = 136
HOURLY_COLUMNS = 72
HIGH_BLOCK_START = 80
LOW_BLOCK_START = 108
BLOCK_LENGTH = 28
ENTRY_LENGTH = 7
ENTRIES_PER_BLOCK = 4


@dataclass(frozen=True)
class JMASuisanDaily:
    """Daily high/low tide entries from JMA suisan text.

    気象庁の推算テキストから抽出した日別の満干潮情報を保持します。

    Attributes:
        date (date): Target date.
                     (対象日)
        station_id (str): JMA station code.
                          (地点記号)
        highs (list[tuple[time, int]]): High tide times and heights.
                                        (満潮の時刻と潮位)
        lows (list[tuple[time, int]]): Low tide times and heights.
                                       (干潮の時刻と潮位)
    """

    date: date
    station_id: str
    highs: list[tuple[time, int]]
    lows: list[tuple[time, int]]


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


def parse_jma_suisan_text(text: str, station_id: str) -> dict[date, JMASuisanDaily]:
    """Parse JMA suisan text into daily high/low tide entries.

    Args:
        text (str): Raw text content from JMA suisan file.
                    (JMA 推算テキストファイルの生テキスト)
        station_id (str): Station code used for filtering.
                          (地点記号)

    Returns:
        dict[date, JMASuisanDaily]: Mapping of date to daily entries.
                                    (日付 -> 満干潮情報の辞書)
    """
    daily_map: dict[date, JMASuisanDaily] = {}
    raw_lines = text.strip("\n\r").split("\n") if "\n" in text else []
    if not raw_lines:
        raw_lines = [text[i : i + LINE_LENGTH] for i in range(0, len(text), LINE_LENGTH)]

    for line in raw_lines:
        if len(line) < LOW_BLOCK_START + BLOCK_LENGTH:
            continue

        year_str = line[72:74].strip()
        month_str = line[74:76].strip()
        day_str = line[76:78].strip()
        station = line[78:80].strip()

        if not year_str or not month_str or not day_str:
            continue

        try:
            target_date = date(2000 + int(year_str), int(month_str), int(day_str))
        except ValueError:
            logger.debug("日付パースエラー: %s", line[72:80])
            continue

        if station and station != station_id:
            continue

        highs = _parse_time_height_block(line, HIGH_BLOCK_START)
        lows = _parse_time_height_block(line, LOW_BLOCK_START)

        if target_date not in daily_map:
            daily_map[target_date] = JMASuisanDaily(
                date=target_date,
                station_id=station_id,
                highs=[],
                lows=[],
            )

        daily_map[target_date].highs.extend(highs)
        daily_map[target_date].lows.extend(lows)

    return daily_map


def _parse_time_height_block(line: str, block_start: int) -> list[tuple[time, int]]:
    """Parse a block of time/height entries.

    時刻・潮位のブロックをパースして満干潮のエントリを抽出します。

    Args:
        line (str): Raw line.
        block_start (int): Start index for the block.

    Returns:
        list[tuple[time, int]]: Parsed time/height entries.
    """
    entries: list[tuple[time, int]] = []
    block = line[block_start : block_start + BLOCK_LENGTH]
    for i in range(ENTRIES_PER_BLOCK):
        entry = block[i * ENTRY_LENGTH : (i + 1) * ENTRY_LENGTH]
        time_str = entry[0:4].strip()
        height_str = entry[4:7].strip()
        if not time_str or not height_str:
            continue
        if time_str == "9999" or height_str == "999":
            continue
        try:
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
            height_cm = int(height_str)
        except ValueError:
            continue
        try:
            entries.append((time(hour, minute), height_cm))
        except ValueError:
            continue
    return entries


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

    summary = parse_jma_suisan_text(text, args.station)
    logger.info("保存完了: %s (日数=%d)", output_path, len(summary))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
