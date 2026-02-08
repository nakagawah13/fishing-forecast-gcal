"""Integration test against JMA suisan data.

This test compares predicted high/low tides with JMA suisan text data.
JMA の推算テキストと照合し、満干潮が欠落しないことを確認します。
"""

from __future__ import annotations

import os
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from scripts.fetch_jma_suisan_tide_data import parse_jma_suisan_text

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import TideEvent
from fishing_forecast_gcal.domain.services.tide_calculation_service import TideCalculationService
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
)

JST = ZoneInfo("Asia/Tokyo")

TARGET_DATE = date(2026, 2, 18)
DEFAULT_TOLERANCE_MINUTES = 10


@pytest.mark.integration
def test_suisan_high_low_matches_target_date() -> None:
    """Ensure high/low tides match JMA suisan within tolerance.

    JMA 推算テキストを用いて、対象日の満干潮が欠落しないことを確認します。
    """
    suisan_path = os.getenv("JMA_SUISAN_TEXT_PATH")
    if not suisan_path:
        pytest.skip("JMA_SUISAN_TEXT_PATH が未設定のためスキップ")

    path = Path(suisan_path)
    if not path.exists():
        pytest.skip(f"指定されたファイルが存在しません: {path}")

    station_id = os.getenv("JMA_SUISAN_STATION_ID", "TK").upper()
    tolerance = int(os.getenv("JMA_SUISAN_TOLERANCE_MIN", str(DEFAULT_TOLERANCE_MINUTES)))
    harmonics_dir = Path(os.getenv("JMA_HARMONICS_DIR", "config/harmonics"))
    harmonics_file = harmonics_dir / f"{station_id.lower()}.pkl"

    if not harmonics_file.exists():
        pytest.skip(f"調和定数ファイルが存在しません: {harmonics_file}")

    text = path.read_text(encoding="utf-8")
    daily_map = parse_jma_suisan_text(text, station_id)

    if TARGET_DATE not in daily_map:
        pytest.fail(f"対象日がデータに含まれていません: {TARGET_DATE}")

    expected = daily_map[TARGET_DATE]
    if len(expected.highs) < 2 or len(expected.lows) < 2:
        pytest.fail("JMA 推算データに満干潮が不足しています")

    location = Location(
        id="jma_target",
        name="JMA Target",
        latitude=35.65,
        longitude=139.77,
        station_id=station_id,
    )
    adapter = TideCalculationAdapter(harmonics_dir)
    service = TideCalculationService()

    tide_data = adapter.calculate_tide(location, TARGET_DATE)
    events = service.extract_high_low_tides(tide_data)

    events_for_day = [event for event in events if event.time.astimezone(JST).date() == TARGET_DATE]

    highs = [event for event in events_for_day if event.event_type == "high"]
    lows = [event for event in events_for_day if event.event_type == "low"]

    assert len(highs) >= 2, "満潮が2回未満です"
    assert len(lows) >= 2, "干潮が2回未満です"

    for expected_time, _height in expected.highs[:2]:
        _assert_time_match(
            TARGET_DATE,
            expected_time,
            highs,
            tolerance,
            label="満潮",
        )

    for expected_time, _height in expected.lows[:2]:
        _assert_time_match(
            TARGET_DATE,
            expected_time,
            lows,
            tolerance,
            label="干潮",
        )


def _assert_time_match(
    target_date: date,
    expected_time: time,
    events: list[TideEvent],
    tolerance_minutes: int,
    label: str,
) -> None:
    """Assert that at least one event matches the expected time.

    期待時刻に一致する満干潮が存在することを確認します。

    Args:
        target_date (date): Target date.
                            (対象日)
        expected_time (datetime.time): Expected time in JST.
                                       (JSTの期待時刻)
        events (list): List of TideEvent.
                       (TideEventのリスト)
        tolerance_minutes (int): Allowed minutes difference.
                                 (許容差分)
        label (str): Label for error messages.
                     (エラーメッセージ用ラベル)
    """
    expected_dt = datetime.combine(target_date, expected_time, tzinfo=JST)
    min_diff = min(
        abs((event.time.astimezone(JST) - expected_dt).total_seconds()) / 60.0 for event in events
    )
    assert min_diff <= tolerance_minutes, (
        f"{label}が一致しません: expected={expected_dt.time()}, diff={min_diff:.1f}min"
    )
