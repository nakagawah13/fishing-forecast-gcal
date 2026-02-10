#!/usr/bin/env python3
"""Fetch JMA tidal observation data and generate harmonic coefficients.

気象庁（JMA）の潮汐観測データをダウンロードし、UTide solve() で
調和解析を行い、TideCalculationAdapter 用の pickle ファイルを生成します。

このスクリプトは CLI エントリーポイントです。
コアロジックは src/fishing_forecast_gcal/infrastructure/jma/ に実装されています。

Usage:
    uv run python scripts/fetch_jma_tide_data.py --station TK --year 2025
    uv run python scripts/fetch_jma_tide_data.py --station TK --year 2024 --months 1-12
    uv run python scripts/fetch_jma_tide_data.py --list-stations

Data Source:
    気象庁 潮汐観測資料
    https://www.data.jma.go.jp/kaiyou/db/tide/genbo/index.php

Reference:
    JMAtide (MATLAB, MIT License): https://github.com/hydrocoast/JMAtide
    URL パターン・テキストフォーマット解析を参考にしています。
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from fishing_forecast_gcal.infrastructure.jma import (
    STATIONS,
    fetch_and_parse_observation_data,
    run_harmonic_analysis,
)

logger = logging.getLogger(__name__)


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
