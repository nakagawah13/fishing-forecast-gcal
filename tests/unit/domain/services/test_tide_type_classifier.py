"""TideTypeClassifierのユニットテスト"""

import pytest

from fishing_forecast_gcal.domain.models.tide import TideType
from fishing_forecast_gcal.domain.services.tide_type_classifier import TideTypeClassifier


class TestTideTypeClassifier:
    """TideTypeClassifierクラスのテスト"""

    def test_classify_spring_tide_new_moon(self) -> None:
        """新月付近（月齢0）は大潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=0.0)
        assert result == TideType.SPRING

    def test_classify_spring_tide_new_moon_before(self) -> None:
        """新月前（月齢27）は大潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=27.0)
        assert result == TideType.SPRING

    def test_classify_spring_tide_new_moon_after(self) -> None:
        """新月後（月齢3）は大潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=3.0)
        assert result == TideType.SPRING

    def test_classify_spring_tide_full_moon(self) -> None:
        """満月付近（月齢15）は大潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=15.0)
        assert result == TideType.SPRING

    def test_classify_spring_tide_full_moon_before(self) -> None:
        """満月前（月齢12）は大潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=12.0)
        assert result == TideType.SPRING

    def test_classify_spring_tide_full_moon_after(self) -> None:
        """満月後（月齢18）は大潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=18.0)
        assert result == TideType.SPRING

    def test_classify_neap_tide_first_quarter(self) -> None:
        """上弦付近（月齢7）は小潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=80.0, moon_age=7.0)
        assert result == TideType.NEAP

    def test_classify_neap_tide_first_quarter_before(self) -> None:
        """上弦前（月齢5）は小潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=80.0, moon_age=5.0)
        assert result == TideType.NEAP

    def test_classify_neap_tide_last_quarter(self) -> None:
        """下弦付近（月齢22）は小潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=80.0, moon_age=22.0)
        assert result == TideType.NEAP

    def test_classify_neap_tide_last_quarter_before(self) -> None:
        """下弦前（月齢20）は小潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=80.0, moon_age=20.0)
        assert result == TideType.NEAP

    def test_classify_long_tide_after_first_quarter(self) -> None:
        """上弦1-2日後（月齢8-9）は長潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=70.0, moon_age=8.0)
        assert result == TideType.LONG

    def test_classify_long_tide_after_last_quarter(self) -> None:
        """下弦1-2日後（月齢23-24）は長潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=70.0, moon_age=23.0)
        assert result == TideType.LONG

    def test_classify_young_tide_after_long_first(self) -> None:
        """長潮の翌日（月齢9-10）は若潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=90.0, moon_age=9.5)
        assert result == TideType.YOUNG

    def test_classify_young_tide_after_long_last(self) -> None:
        """長潮の翌日（月齢24-25）は若潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=90.0, moon_age=24.5)
        assert result == TideType.YOUNG

    def test_classify_moderate_tide_between_spring_and_neap(self) -> None:
        """大潮と小潮の間（月齢4、19、25）は中潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=120.0, moon_age=4.0)
        assert result == TideType.MODERATE

    def test_classify_moderate_tide_between_young_and_spring(self) -> None:
        """若潮と大潮の間（月齢10-12）は中潮と判定される"""
        result = TideTypeClassifier.classify(tide_range_cm=130.0, moon_age=11.0)
        assert result == TideType.MODERATE

    def test_classify_boundary_moon_age_zero(self) -> None:
        """月齢0付近の境界テスト"""
        # 月齢29.5は新月に近いので大潮
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=29.5)
        assert result == TideType.SPRING

    def test_classify_boundary_moon_age_wrap(self) -> None:
        """月齢の境界（0と29.5の間）のテスト"""
        # 月齢26.5以上は新月前なので大潮
        result = TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=26.5)
        assert result == TideType.SPRING

    def test_classify_with_large_tide_range(self) -> None:
        """潮位差が大きい場合、大潮方向に補正される"""
        # 月齢4は通常中潮だが、潮位差が大きいので大潮に補正
        result = TideTypeClassifier.classify(tide_range_cm=200.0, moon_age=4.0)
        assert result == TideType.SPRING

    def test_classify_with_small_tide_range(self) -> None:
        """潮位差が小さい場合、小潮方向に補正される"""
        # 月齢3は通常大潮だが、潮位差が小さいので中潮に補正
        result = TideTypeClassifier.classify(tide_range_cm=60.0, moon_age=3.0)
        assert result == TideType.MODERATE

    def test_classify_invalid_negative_tide_range(self) -> None:
        """潮位差が負の値の場合はエラー"""
        with pytest.raises(ValueError, match="tide_range_cm must be non-negative"):
            TideTypeClassifier.classify(tide_range_cm=-10.0, moon_age=15.0)

    def test_classify_invalid_negative_moon_age(self) -> None:
        """月齢が負の値の場合はエラー"""
        with pytest.raises(ValueError, match="moon_age must be between 0 and 29.5"):
            TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=-1.0)

    def test_classify_invalid_moon_age_over_limit(self) -> None:
        """月齢が30以上の場合はエラー"""
        with pytest.raises(ValueError, match="moon_age must be between 0 and 29.5"):
            TideTypeClassifier.classify(tide_range_cm=150.0, moon_age=30.0)
