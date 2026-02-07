#!/usr/bin/env python3
"""Fetch JMA tidal observation data and generate harmonic coefficients.

気象庁（JMA）の潮汐観測データをダウンロードし、UTide solve() で
調和解析を行い、TideCalculationAdapter 用の pickle ファイルを生成します。

Usage:
    uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025
    uv run python scripts/fetch_jma_tide_data.py --station TK --year 2024 --months 1-12
    uv run python scripts/fetch_jma_tide_data.py --list-stations

Data Source:
    気象庁 潮汐観測資料
    https://www.data.jma.go.jp/kaiyou/db/tide/genbo/index.php
    テキストファイルフォーマット:
    https://www.data.jma.go.jp/gmd/kaiyou/db/tide/genbo/format.html

Reference:
    JMAtide (MATLAB, MIT License): https://github.com/hydrocoast/JMAtide
    URL パターン・テキストフォーマット解析を参考にしています。
"""

from __future__ import annotations

import argparse
import logging
import pickle
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

try:
    import httpx
except ImportError:
    print("httpx が必要です: uv add httpx", file=sys.stderr)
    sys.exit(1)

try:
    import utide
except ImportError:
    print("utide が必要です: uv add utide", file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger(__name__)

# JMA data URL templates
# 観測潮位（確定値）: 毎時潮位テキストファイル
JMA_OBS_URL_TEMPLATE = (
    "https://www.data.jma.go.jp/gmd/kaiyou/data/db/tide/genbo"
    "/{year}/{year}{month:02d}/hry{year}{month:02d}{station}.txt"
)

# リクエスト間隔（秒）- JMA サーバーへの負荷軽減
REQUEST_INTERVAL_SEC = 1.0

# テキストフォーマット定数（1行 = 1日、137文字固定長）
LINE_LENGTH = 137
HOURLY_COLUMNS = 72  # 3桁 × 24時間 (0:00-23:00)
HOURS_PER_DAY = 24
DIGITS_PER_HOUR = 3


@dataclass(frozen=True)
class JMAStation:
    """JMA tidal observation station information.

    気象庁の潮汐観測地点情報。

    Attributes:
        id (str): Station code (2-character, e.g. 'TK').
                  (地点記号、2文字)
        name (str): Station name in Japanese.
                    (地点名、日本語)
        latitude (float): Station latitude in degrees.
                          (緯度)
        longitude (float): Station longitude in degrees.
                           (経度)
        ref_level_tp_cm (float): Observation reference level relative to T.P. in cm.
                                 (観測基準面の標高、T.P.基準、cm)
    """

    id: str
    name: str
    latitude: float
    longitude: float
    ref_level_tp_cm: float


# 主要な観測地点（JMAtide リポジトリおよび気象庁地点一覧表より）
# ref_level_tp_cm は気象庁の観測地点一覧表の値
STATIONS: dict[str, JMAStation] = {
    "TK": JMAStation("TK", "東京", 35.650, 139.770, -188.40),
    "MR": JMAStation("MR", "布良", 34.917, 139.833, -96.40),
    "OK": JMAStation("OK", "岡田", 34.783, 139.383, -85.30),
    "OD": JMAStation("OD", "小田原", 35.233, 139.150, -94.60),
    "SM": JMAStation("SM", "清水港", 35.017, 138.517, -67.20),
    "OM": JMAStation("OM", "御前崎", 34.617, 138.217, -66.00),
    "OS": JMAStation("OS", "大阪", 34.650, 135.433, -76.60),
    "KB": JMAStation("KB", "神戸", 34.683, 135.183, -82.20),
    "HK": JMAStation("HK", "函館", 41.783, 140.717, -72.90),
    "KR": JMAStation("KR", "釧路", 42.983, 144.367, -90.40),
    "NG": JMAStation("NG", "名古屋", 35.083, 136.883, -124.20),
    "ON": JMAStation("ON", "小名浜", 36.933, 140.900, -99.30),
    "KS": JMAStation("KS", "串本", 33.483, 135.767, -94.50),
    "FK": JMAStation("FK", "福岡", 33.617, 130.400, -192.10),
    "HA": JMAStation("HA", "博多", 33.617, 130.400, -192.10),
    "NS": JMAStation("NS", "長崎", 32.733, 129.867, -160.00),
    "NH": JMAStation("NH", "那覇", 26.217, 127.667, -95.70),
}


def parse_jma_hourly_text(text: str, station_id: str) -> list[tuple[datetime, float]]:
    """Parse JMA hourly tide observation text data.

    気象庁の毎時潮位テキストデータをパースし、(datetime, height_cm) のリストを返します。
    潮位は観測基準面上の値（cm）です。

    Format (1 line = 1 day, 137 chars fixed-width):
        Columns 1-72:  Hourly heights (3 digits × 24 hours, 0:00-23:00)
        Columns 73-74: Year (last 2 digits)
        Columns 75-76: Month
        Columns 77-78: Day
        Columns 79-80: Station code

    Args:
        text (str): Raw text content from JMA hourly tide file.
                    (JMA 毎時潮位テキストファイルの生テキスト)
        station_id (str): Expected station code for validation.
                          (検証用の地点コード)

    Returns:
        list[tuple[datetime, float]]: Parsed (UTC-aware datetime, height_cm) pairs.
            Missing values (blank fields) are excluded.
            (パース済みの時刻・潮位ペア。欠測値は除外)

    Raises:
        ValueError: If text format is invalid or station code mismatch.
                    (テキスト形式が不正な場合)
    """
    results: list[tuple[datetime, float]] = []
    # JMA のテキストデータの改行コードは LF
    # ただし webread で取得すると改行なしの固定長テキストの場合もある
    # 行単位でもバイト列でも対応

    # 改行がある場合は行ごとに処理
    lines = text.strip().split("\n") if "\n" in text else []

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


def fetch_monthly_data(
    station_id: str,
    year: int,
    month: int,
    client: httpx.Client,
) -> str:
    """Fetch one month of hourly tide data from JMA.

    気象庁から1ヶ月分の毎時潮位データをダウンロードします。

    Args:
        station_id (str): JMA station code (e.g. 'TK').
                          (JMA 地点記号)
        year (int): Target year (>= 1997).
                    (対象年)
        month (int): Target month (1-12).
                     (対象月)
        client (httpx.Client): HTTP client instance.
                               (HTTPクライアント)

    Returns:
        str: Raw text content of the JMA hourly tide file.
             (JMA 毎時潮位テキストファイルの内容)

    Raises:
        httpx.HTTPStatusError: If the request fails (404, 500, etc.).
                               (リクエスト失敗時)
    """
    url = JMA_OBS_URL_TEMPLATE.format(year=year, month=month, station=station_id)
    logger.info("ダウンロード中: %s", url)
    response = client.get(url, timeout=30.0)
    response.raise_for_status()
    return response.text


def fetch_and_parse_observation_data(
    station_id: str,
    year: int,
    months: list[int],
) -> list[tuple[datetime, float]]:
    """Fetch and parse multiple months of JMA observation data.

    複数月分の JMA 観測潮位データを取得・パースして結合します。

    Args:
        station_id (str): JMA station code.
                          (JMA 地点記号)
        year (int): Target year.
                    (対象年)
        months (list[int]): List of months to fetch (1-12).
                            (取得対象の月リスト)

    Returns:
        list[tuple[datetime, float]]: Combined observation data sorted by time.
            (時刻順にソートされた結合済み観測データ)
    """
    all_data: list[tuple[datetime, float]] = []

    with httpx.Client() as client:
        for month in months:
            try:
                text = fetch_monthly_data(station_id, year, month, client)
                monthly_data = parse_jma_hourly_text(text, station_id)
                all_data.extend(monthly_data)
                logger.info(
                    "取得完了: %d年%d月, %dデータポイント",
                    year,
                    month,
                    len(monthly_data),
                )
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "取得失敗: %d年%d月 (%s)",
                    year,
                    month,
                    e.response.status_code,
                )
                continue

            # JMA サーバーへの負荷軽減
            time.sleep(REQUEST_INTERVAL_SEC)

    # 時刻順にソート
    all_data.sort(key=lambda x: x[0])
    logger.info(
        "全データ取得完了: station=%s, 総データポイント数=%d",
        station_id,
        len(all_data),
    )
    return all_data


def run_harmonic_analysis(
    observation_data: list[tuple[datetime, float]],
    latitude: float,
    output_path: Path,
) -> dict[str, Any]:
    """Run UTide harmonic analysis and save coefficients as pickle.

    観測データから UTide solve() で調和解析を実行し、
    pickle ファイルとして保存します。

    Args:
        observation_data (list[tuple[datetime, float]]): Observed (time, height_cm) pairs.
            (観測データの (時刻, 潮位cm) ペア)
        latitude (float): Station latitude.
                          (観測地点の緯度)
        output_path (Path): Path to save the pickle file.
                            (pickle 保存先パス)

    Returns:
        dict[str, Any]: UTide coefficient object (Bunch).
                        (UTide 調和定数オブジェクト)

    Raises:
        ValueError: If observation data is insufficient.
                    (観測データが不足している場合)
        RuntimeError: If harmonic analysis fails.
                      (調和解析に失敗した場合)
    """
    if len(observation_data) < 168:
        raise ValueError(
            f"観測データが不足しています: {len(observation_data)}点 (最低168点=1週間分が必要)"
        )

    # numpy 配列に変換
    times_list = [t for t, _ in observation_data]
    heights_list = [h for _, h in observation_data]

    times_array = np.array(times_list, dtype="datetime64[ns]")
    heights_array = np.array(heights_list, dtype=np.float64)

    # UTide 調和解析
    logger.info(
        "調和解析を実行中: データポイント数=%d, 緯度=%.3f",
        len(times_array),
        latitude,
    )

    try:
        coef: dict[str, Any] = utide.solve(
            times_array,
            heights_array,
            lat=latitude,
            verbose=False,
        )
    except Exception as e:
        raise RuntimeError(f"調和解析に失敗しました: {e}") from e

    # pickle で保存
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(coef, f)

    # 結果サマリー
    n_constituents = len(coef["name"])
    mean_height = float(coef["mean"])
    constituent_pairs: list[tuple[str, float]] = list(zip(coef["name"], coef["A"], strict=True))
    top_constituents = sorted(
        constituent_pairs,
        key=lambda x: x[1],
        reverse=True,
    )[:10]

    logger.info("調和解析完了:")
    logger.info("  出力ファイル: %s", output_path)
    logger.info("  分潮数: %d", n_constituents)
    logger.info("  平均潮位: %.2f cm", mean_height)
    logger.info("  主要分潮 (上位10):")
    for name, amplitude in top_constituents:
        logger.info("    %s: 振幅 = %.2f cm", name, amplitude)

    return coef


def list_stations() -> None:
    """Print available JMA stations.

    利用可能な JMA 観測地点の一覧を表示します。
    """
    print(f"\n{'コード':>6}  {'地点名':<12}  {'緯度':>8}  {'経度':>8}  {'基準面(T.P.)':>12}")
    print("-" * 60)
    for station in STATIONS.values():
        print(
            f"{station.id:>6}  {station.name:<12}  "
            f"{station.latitude:>8.3f}  {station.longitude:>8.3f}  "
            f"{station.ref_level_tp_cm:>10.1f} cm"
        )
    print()


def main() -> None:
    """Entry point for the JMA tide data fetch script.

    コマンドライン引数をパースし、データ取得 → 調和解析 → pickle 保存を実行します。
    """
    parser = argparse.ArgumentParser(
        description="気象庁の潮汐観測データを取得し、UTide 調和定数を生成します。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 東京(TK) の 2025年全月データで調和定数を生成
  uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025

  # 特定の月のみ取得
  uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025 --months 1-6

  # 利用可能な地点一覧を表示
  uv run python scripts/fetch_jma_tide_data.py --list-stations

  # 出力先を指定
  uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025 -o config/harmonics/tokyo.pkl
        """,
    )

    parser.add_argument(
        "--station",
        type=str,
        help="JMA 地点記号 (例: TK=東京, MR=布良, OK=岡田)",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="取得対象年 (1997以降)",
    )
    parser.add_argument(
        "--months",
        type=str,
        default="1-12",
        help="取得対象月の範囲 (デフォルト: 1-12)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="出力先 pickle ファイルパス (デフォルト: config/harmonics/{station_id}.pkl)",
    )
    parser.add_argument(
        "--list-stations",
        action="store_true",
        help="利用可能な地点一覧を表示",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細ログを表示",
    )

    args = parser.parse_args()

    # ログ設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 地点一覧表示
    if args.list_stations:
        list_stations()
        return

    # 引数チェック
    if not args.station or not args.year:
        parser.error("--station と --year は必須です (--list-stations で地点一覧を確認)")

    station_id = args.station.upper()
    if station_id not in STATIONS:
        logger.warning(
            "地点 '%s' は登録済みリストにありませんが、JMA にデータがあれば取得を試みます。",
            station_id,
        )
        # 未登録でも取得は試行する（緯度はユーザー指定が必要）

    # 月の範囲をパース
    months_str: str = args.months
    if "-" in months_str:
        parts = months_str.split("-")
        month_start = int(parts[0])
        month_end = int(parts[1])
        months = list(range(month_start, month_end + 1))
    else:
        months = [int(m) for m in months_str.split(",")]

    # 出力先パスの決定
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("config/harmonics") / f"{station_id.lower()}.pkl"

    # 地点情報の取得
    station = STATIONS.get(station_id)
    if station:
        latitude = station.latitude
        logger.info("地点: %s (%s), 緯度: %.3f", station.name, station.id, latitude)
    else:
        # 未登録地点の場合、デフォルト緯度を使用（東京湾近辺）
        latitude = 35.0
        logger.warning("未登録地点のため、デフォルト緯度 %.1f を使用します。", latitude)

    # データ取得
    logger.info("=" * 60)
    logger.info("JMA 潮汐観測データ取得開始")
    logger.info("  地点: %s", station_id)
    logger.info("  年: %d", args.year)
    logger.info("  月: %s", months)
    logger.info("  出力先: %s", output_path)
    logger.info("=" * 60)

    observation_data = fetch_and_parse_observation_data(station_id, args.year, months)

    if not observation_data:
        logger.error("観測データが取得できませんでした。地点コード・年月を確認してください。")
        sys.exit(1)

    # 調和解析の実行
    coef = run_harmonic_analysis(observation_data, latitude, output_path)

    # 完了メッセージ
    logger.info("=" * 60)
    logger.info("処理完了!")
    logger.info("  pickle ファイル: %s", output_path)
    logger.info("  分潮数: %d", len(coef["name"]))
    logger.info("  平均潮位: %.2f cm (観測基準面上)", float(coef["mean"]))
    logger.info("")
    logger.info("使用方法:")
    logger.info("  このファイルは TideCalculationAdapter で自動的に読み込まれます。")
    logger.info("  config/harmonics/ に配置してください。")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
