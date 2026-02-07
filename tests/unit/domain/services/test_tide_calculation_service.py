"""TideCalculationService のユニットテスト"""

from datetime import UTC, datetime

from fishing_forecast_gcal.domain.services.tide_calculation_service import (
    TideCalculationService,
)


class TestTideCalculationService:
    """TideCalculationService のテストクラス"""

    def test_extract_high_low_tides_from_typical_data(self) -> None:
        """典型的な潮汐データから満干潮を抽出できること"""
        # Arrange: 典型的な1日の潮汐データ（1時間ごと）
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),  # 干潮に向かう
            (base_time.replace(hour=1), 80.0),
            (base_time.replace(hour=2), 60.0),  # 干潮
            (base_time.replace(hour=3), 80.0),
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 120.0),
            (base_time.replace(hour=6), 140.0),
            (base_time.replace(hour=7), 160.0),  # 満潮
            (base_time.replace(hour=8), 140.0),
            (base_time.replace(hour=9), 120.0),
            (base_time.replace(hour=10), 100.0),
            (base_time.replace(hour=11), 80.0),
            (base_time.replace(hour=12), 60.0),  # 干潮
            (base_time.replace(hour=13), 80.0),
            (base_time.replace(hour=14), 100.0),
            (base_time.replace(hour=15), 120.0),
            (base_time.replace(hour=16), 140.0),
            (base_time.replace(hour=17), 150.0),  # 満潮
            (base_time.replace(hour=18), 140.0),
            (base_time.replace(hour=19), 120.0),
            (base_time.replace(hour=20), 100.0),
            (base_time.replace(hour=21), 90.0),
            (base_time.replace(hour=22), 85.0),
            (base_time.replace(hour=23), 83.0),
        ]

        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 満潮2回、干潮2回が検出されること
        assert len(result) == 4

        # 時系列順に並んでいること
        assert result[0].time == base_time.replace(hour=2)
        assert result[0].event_type == "low"
        assert result[0].height_cm == 60.0

        assert result[1].time == base_time.replace(hour=7)
        assert result[1].event_type == "high"
        assert result[1].height_cm == 160.0

        assert result[2].time == base_time.replace(hour=12)
        assert result[2].event_type == "low"
        assert result[2].height_cm == 60.0

        assert result[3].time == base_time.replace(hour=17)
        assert result[3].event_type == "high"
        assert result[3].height_cm == 150.0

    def test_extract_high_low_tides_with_empty_data(self) -> None:
        """空のデータから空リストを返すこと"""
        # Arrange
        data: list[tuple[datetime, float]] = []
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_insufficient_data_one_point(self) -> None:
        """データが1点のみの場合、空リストを返すこと"""
        # Arrange
        data = [(datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC), 100.0)]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_insufficient_data_two_points(self) -> None:
        """データが2点のみの場合、空リストを返すこと"""
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time, 100.0),
            (base_time.replace(hour=1), 120.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_flat_data(self) -> None:
        """全て同じ値のフラットなデータの場合、空リストを返すこと"""
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [(base_time.replace(hour=i), 100.0) for i in range(24)]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert
        assert result == []

    def test_extract_high_low_tides_with_out_of_range_values(self) -> None:
        """範囲外の潮位を含む場合、その極値をスキップすること"""
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 80.0),
            (base_time.replace(hour=2), -10.0),  # 範囲外（負の値）
            (base_time.replace(hour=3), 80.0),
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 120.0),
            (base_time.replace(hour=6), 600.0),  # 範囲外（500cm超）
            (base_time.replace(hour=7), 120.0),
            (base_time.replace(hour=8), 100.0),
            (base_time.replace(hour=9), 80.0),
            (base_time.replace(hour=10), 60.0),  # 有効な干潮
            (base_time.replace(hour=11), 80.0),
            (base_time.replace(hour=12), 100.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 有効な極値（hour=10の干潮）のみ検出されること
        assert len(result) == 1
        assert result[0].time == base_time.replace(hour=10)
        assert result[0].event_type == "low"
        assert result[0].height_cm == 60.0

    def test_extract_high_low_tides_preserves_order(self) -> None:
        """抽出結果が時系列順に並んでいること"""
        # Arrange
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 60.0),  # 干潮
            (base_time.replace(hour=2), 100.0),
            (base_time.replace(hour=3), 160.0),  # 満潮
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 50.0),  # 干潮
            (base_time.replace(hour=6), 100.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 時系列順であること
        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i].time < result[i + 1].time

    def test_extract_high_low_tides_with_multiple_peaks_in_sequence(self) -> None:
        """極値が連続する場合でも正しく検出できること"""
        # Arrange: ピークが連続するケース
        base_time = datetime(2026, 2, 8, 0, 0, 0, tzinfo=UTC)
        data = [
            (base_time.replace(hour=0), 100.0),
            (base_time.replace(hour=1), 120.0),  # 極大（満潮）
            (base_time.replace(hour=2), 100.0),  # 極小（干潮）
            (base_time.replace(hour=3), 110.0),  # 極大（満潮）
            (base_time.replace(hour=4), 100.0),
            (base_time.replace(hour=5), 80.0),
            (base_time.replace(hour=6), 60.0),  # 極小（干潮）
            (base_time.replace(hour=7), 80.0),
        ]
        service = TideCalculationService()

        # Act
        result = service.extract_high_low_tides(data)

        # Assert: 全ての極値が検出されること（満潮2回、干潮2回）
        assert len(result) == 4
        assert result[0].time == base_time.replace(hour=1)
        assert result[0].event_type == "high"
        assert result[1].time == base_time.replace(hour=2)
        assert result[1].event_type == "low"
        assert result[2].time == base_time.replace(hour=3)
        assert result[2].event_type == "high"
        assert result[3].time == base_time.replace(hour=6)
        assert result[3].event_type == "low"
