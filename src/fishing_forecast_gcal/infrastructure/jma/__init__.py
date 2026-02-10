"""JMA tidal observation infrastructure package.

気象庁(JMA)の潮汐観測データに関するインフラストラクチャモジュール。
地点情報、毎時潮位テキストパーサー、調和解析パイプラインを提供します。

Reference:
    https://www.data.jma.go.jp/kaiyou/db/tide/genbo/station.php
"""

from fishing_forecast_gcal.infrastructure.jma.harmonic_analysis import (
    fetch_and_parse_observation_data,
    fetch_monthly_data,
    run_harmonic_analysis,
)
from fishing_forecast_gcal.infrastructure.jma.hourly_text_parser import (
    parse_jma_hourly_text,
)
from fishing_forecast_gcal.infrastructure.jma.stations import (
    STATIONS,
    JMAStation,
)

__all__ = [
    "STATIONS",
    "JMAStation",
    "fetch_and_parse_observation_data",
    "fetch_monthly_data",
    "parse_jma_hourly_text",
    "run_harmonic_analysis",
]
