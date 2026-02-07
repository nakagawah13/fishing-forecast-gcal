"""釣行条件モデルのテスト"""

import dataclasses
from datetime import UTC, datetime

import pytest

from fishing_forecast_gcal.domain.models.fishing_condition import FishingCondition


class TestFishingCondition:
    """FishingConditionモデルのテスト"""

    def test_create_valid_fishing_condition(self) -> None:
        """正常な釣行条件を作成できること"""
        condition = FishingCondition(
            wind_speed_mps=5.0,
            wind_direction="北",
            pressure_hpa=1012.0,
            forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
            warning_level="safe"
        )
        assert condition.wind_speed_mps == 5.0
        assert condition.wind_direction == "北"
        assert condition.pressure_hpa == 1012.0
        assert condition.warning_level == "safe"

    def test_wind_speed_negative_raises_error(self) -> None:
        """負の風速でエラーが発生すること"""
        with pytest.raises(ValueError, match="wind_speed_mps must be between 0 and 50"):
            FishingCondition(
                wind_speed_mps=-1.0,
                wind_direction="北",
                pressure_hpa=1012.0,
                forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                warning_level="safe"
            )

    def test_wind_speed_over_50_raises_error(self) -> None:
        """50m/sを超える風速でエラーが発生すること"""
        with pytest.raises(ValueError, match="wind_speed_mps must be between 0 and 50"):
            FishingCondition(
                wind_speed_mps=51.0,
                wind_direction="北",
                pressure_hpa=1012.0,
                forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                warning_level="safe"
            )

    def test_pressure_below_900_raises_error(self) -> None:
        """900hPa未満の気圧でエラーが発生すること"""
        with pytest.raises(ValueError, match="pressure_hpa must be between 900 and 1100"):
            FishingCondition(
                wind_speed_mps=5.0,
                wind_direction="北",
                pressure_hpa=899.0,
                forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                warning_level="safe"
            )

    def test_pressure_over_1100_raises_error(self) -> None:
        """1100hPaを超える気圧でエラーが発生すること"""
        with pytest.raises(ValueError, match="pressure_hpa must be between 900 and 1100"):
            FishingCondition(
                wind_speed_mps=5.0,
                wind_direction="北",
                pressure_hpa=1101.0,
                forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                warning_level="safe"
            )

    def test_forecast_time_without_timezone_raises_error(self) -> None:
        """timezoneなしの予報時刻でエラーが発生すること"""
        with pytest.raises(ValueError, match="forecast_time must be timezone-aware"):
            FishingCondition(
                wind_speed_mps=5.0,
                wind_direction="北",
                pressure_hpa=1012.0,
                forecast_time=datetime(2026, 2, 8, 6, 0),  # No timezone
                warning_level="safe"
            )

    def test_invalid_warning_level_raises_error(self) -> None:
        """不正なwarning_levelでエラーが発生すること"""
        with pytest.raises(ValueError, match="warning_level must be 'safe', 'caution' or 'danger'"):
            FishingCondition(
                wind_speed_mps=5.0,
                wind_direction="北",
                pressure_hpa=1012.0,
                forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
                warning_level="invalid"  # type: ignore
            )

    def test_fishing_condition_is_immutable(self) -> None:
        """FishingConditionが不変であること"""
        condition = FishingCondition(
            wind_speed_mps=5.0,
            wind_direction="北",
            pressure_hpa=1012.0,
            forecast_time=datetime(2026, 2, 8, 6, 0, tzinfo=UTC),
            warning_level="safe"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            condition.wind_speed_mps = 10.0  # type: ignore


class TestDetermineWarningLevel:
    """warning_level自動判定ロジックのテスト"""

    def test_wind_speed_under_7_is_safe(self) -> None:
        """7m/s未満の風速はsafeと判定されること"""
        assert FishingCondition.determine_warning_level(0.0) == "safe"
        assert FishingCondition.determine_warning_level(3.5) == "safe"
        assert FishingCondition.determine_warning_level(6.9) == "safe"

    def test_wind_speed_7_to_10_is_caution(self) -> None:
        """7-10m/sの風速はcautionと判定されること"""
        assert FishingCondition.determine_warning_level(7.0) == "caution"
        assert FishingCondition.determine_warning_level(8.5) == "caution"
        assert FishingCondition.determine_warning_level(9.9) == "caution"

    def test_wind_speed_10_or_over_is_danger(self) -> None:
        """10m/s以上の風速はdangerと判定されること"""
        assert FishingCondition.determine_warning_level(10.0) == "danger"
        assert FishingCondition.determine_warning_level(15.0) == "danger"
        assert FishingCondition.determine_warning_level(50.0) == "danger"
