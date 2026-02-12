"""Unit tests for MoonAgeCalculator.

MoonAgeCalculator のユニットテストです。
基準新月からの経過日数に基づく月齢計算を検証します。
"""

from datetime import date

from fishing_forecast_gcal.domain.services.moon_age_calculator import MoonAgeCalculator


class TestMoonAgeCalculator:
    """MoonAgeCalculator のユニットテスト"""

    def test_reference_new_moon_date(self) -> None:
        """基準新月（2000年1月6日）の月齢

        00:00 UTC 時点では新月（18:14 UTC）の約18時間前なので、
        月齢は前周期の末尾付近（約29日）になる。
        """
        moon_age = MoonAgeCalculator.calculate(date(2000, 1, 6))
        assert 28 < moon_age < 30

    def test_day_after_reference_new_moon(self) -> None:
        """基準新月の翌日（2000年1月7日）は月齢約1"""
        moon_age = MoonAgeCalculator.calculate(date(2000, 1, 7))
        assert 0 < moon_age < 2

    def test_full_moon_approximately_15_days_later(self) -> None:
        """約15日後（2000年1月21日）は満月付近（月齢約15）"""
        moon_age = MoonAgeCalculator.calculate(date(2000, 1, 21))
        assert 14 < moon_age < 16

    def test_next_cycle_end(self) -> None:
        """約30日後（2000年2月5日）は新月周期末期"""
        moon_age = MoonAgeCalculator.calculate(date(2000, 2, 5))
        assert 28 < moon_age < 30

    def test_next_new_moon(self) -> None:
        """2000年2月6日は次の新月直後"""
        moon_age = MoonAgeCalculator.calculate(date(2000, 2, 6))
        assert 0 <= moon_age < 2

    def test_recent_date(self) -> None:
        """直近の日付で月齢が有効範囲（0-29.53）に収まることを確認"""
        moon_age = MoonAgeCalculator.calculate(date(2026, 2, 8))
        assert 0 <= moon_age < MoonAgeCalculator.MOON_CYCLE_DAYS

    def test_moon_age_is_cyclic(self) -> None:
        """月齢が朔望周期で循環することを確認"""
        # 同じ月齢相当の2日間を比較
        age1 = MoonAgeCalculator.calculate(date(2026, 1, 1))
        age2 = MoonAgeCalculator.calculate(date(2026, 1, 31))
        # 30日差は約1周期なので差は小さいはず
        assert abs(age1 - age2) < 2.0 or abs(age1 - age2) > 27.0
