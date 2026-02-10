"""JMA hourly tide observation text parser.

Parses JMA fixed-width format hourly tidal observation text data.

気象庁の固定長フォーマットの毎時潮位テキストデータをパースします。

Data Source:
    気象庁 潮汐観測資料
    https://www.data.jma.go.jp/kaiyou/db/tide/genbo/index.php

Format Reference:
    https://www.data.jma.go.jp/gmd/kaiyou/db/tide/genbo/format.html
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# テキストフォーマット定数（1行 = 1日、137文字固定長）
LINE_LENGTH = 137
HOURLY_COLUMNS = 72  # 3桁 × 24時間 (0:00-23:00)
HOURS_PER_DAY = 24
DIGITS_PER_HOUR = 3


def parse_jma_hourly_text(text: str, station_id: str) -> list[tuple[datetime, float]]:
    """Parse JMA hourly tide observation text data.

    気象庁の毎時潮位テキストデータをパースし、(datetime, height_cm) のリストを返します。
    潮位は観測基準面上の値（cm）です。

    Format (1 line = 1 day, 137 chars fixed-width):
        Columns 1-72:  Hourly heights (3 digits x 24 hours, 0:00-23:00)
        Columns 73-74: Year (last 2 digits)
        Columns 75-76: Month
        Columns 77-78: Day
        Columns 79-80: Station code

    Args:
        text: Raw text content from JMA hourly tide file.
              (JMA 毎時潮位テキストファイルの生テキスト)
        station_id: Expected station code for validation.
                    (検証用の地点コード)

    Returns:
        Parsed (UTC-aware datetime, height_cm) pairs.
        Missing values (blank fields) are excluded.
        (パース済みの時刻・潮位ペア。欠測値は除外)

    Raises:
        ValueError: If text format is invalid or station code mismatch.
                    (テキスト形式が不正な場合)
    """
    results: list[tuple[datetime, float]] = []

    # 改行がある場合は行ごとに処理
    # Note: strip() ではなく strip("\n\r") を使用。
    # JMA の固定長フォーマットでは行頭のスペースがカラム位置に影響するため、
    # スペースを除去してはいけない。
    lines = text.strip("\n\r").split("\n") if "\n" in text else []

    if lines:
        raw_lines = lines
    else:
        # 改行なしの場合（JMAtide と同じ仕様）: 137文字ごとに分割
        raw_lines = [text[i : i + LINE_LENGTH] for i in range(0, len(text), LINE_LENGTH)]

    for line in raw_lines:
        if len(line) < 80:
            continue

        # 年月日の抽出（カラム 73-78）
        year_2digit = line[72:74].strip()
        month_str = line[74:76].strip()
        day_str = line[76:78].strip()
        stn = line[78:80].strip()

        if not year_2digit or not month_str or not day_str:
            continue

        try:
            year = 2000 + int(year_2digit)
            month = int(month_str)
            day = int(day_str)
        except ValueError:
            logger.warning("日付パースエラー: line='%s'", line[:80])
            continue

        # 地点コード検証（任意）
        if stn and stn != station_id:
            logger.debug("地点コード不一致: expected=%s, got=%s", station_id, stn)

        # 毎時潮位の抽出（カラム 1-72、3桁 × 24時間）
        for hour in range(HOURS_PER_DAY):
            start = hour * DIGITS_PER_HOUR
            end = start + DIGITS_PER_HOUR
            value_str = line[start:end]

            # 空白 = 欠測
            if value_str.strip() == "":
                continue

            try:
                height_cm = float(value_str.strip())
            except ValueError:
                logger.debug(
                    "潮位パースエラー: date=%d-%02d-%02d %02d:00, value='%s'",
                    year,
                    month,
                    day,
                    hour,
                    value_str,
                )
                continue

            # JST (UTC+9) で datetime を生成
            jst = timezone(timedelta(hours=9))
            dt = datetime(year, month, day, hour, 0, 0, tzinfo=jst)
            results.append((dt, height_cm))

    logger.info(
        "パース完了: station=%s, データポイント数=%d",
        station_id,
        len(results),
    )
    return results
