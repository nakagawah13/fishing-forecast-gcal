"""JMA harmonic analysis pipeline.

Provides functions for fetching JMA tidal observation data
and running UTide harmonic analysis to generate coefficients.

気象庁の観測潮位データの取得と UTide 調和解析パイプラインを提供します。

Data Source:
    気象庁 潮汐観測資料
    https://www.data.jma.go.jp/kaiyou/db/tide/genbo/index.php
"""

from __future__ import annotations

import logging
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

try:
    import httpx
except ImportError as _e:
    raise ImportError("httpx が必要です: uv add httpx") from _e

try:
    import utide
except ImportError as _e:
    raise ImportError("utide が必要です: uv add utide") from _e

from fishing_forecast_gcal.infrastructure.jma.hourly_text_parser import (
    parse_jma_hourly_text,
)

logger = logging.getLogger(__name__)

# JMA data URL templates
# 観測潮位（確定値）: 毎時潮位テキストファイル
# Note: 2025年頃に /gmd/kaiyou/ → /kaiyou/ へパス変更された
JMA_OBS_URL_TEMPLATE = (
    "https://www.data.jma.go.jp/kaiyou/data/db/tide/genbo"
    "/{year}/{year}{month:02d}/hry{year}{month:02d}{station}.txt"
)

# リクエスト間隔（秒）- JMA サーバーへの負荷軽減
REQUEST_INTERVAL_SEC = 1.0


def fetch_monthly_data(
    station_id: str,
    year: int,
    month: int,
    client: httpx.Client,
) -> str:
    """Fetch one month of hourly tide data from JMA.

    気象庁から1ヶ月分の毎時潮位データをダウンロードします。

    Args:
        station_id: JMA station code (e.g. 'TK').
                    (JMA 地点記号)
        year: Target year (>= 1997).
              (対象年)
        month: Target month (1-12).
               (対象月)
        client: HTTP client instance.
                (HTTPクライアント)

    Returns:
        Raw text content of the JMA hourly tide file.
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
        station_id: JMA station code.
                    (JMA 地点記号)
        year: Target year.
              (対象年)
        months: List of months to fetch (1-12).
                (取得対象の月リスト)

    Returns:
        Combined observation data sorted by time.
        (時刻順にソートされた結合済み観測データ)
    """
    all_data: list[tuple[datetime, float]] = []

    with httpx.Client(follow_redirects=True) as client:
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
        observation_data: Observed (time, height_cm) pairs.
                          (観測データの (時刻, 潮位cm) ペア)
        latitude: Station latitude.
                  (観測地点の緯度)
        output_path: Path to save the pickle file.
                     (pickle 保存先パス)

    Returns:
        UTide coefficient object (Bunch).
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
