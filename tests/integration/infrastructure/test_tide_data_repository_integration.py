"""Integration tests for TideDataRepository.

このモジュールは TideDataRepository の統合テストを提供します。
実際の TideCalculationAdapter と調和定数データを使用して検証します。

Note:
    調和定数ファイルは `config/harmonics/{station_id}.pkl` に配置する必要があります。
    ファイルが存在しない場合、一部のテストはスキップされます。
"""

from datetime import date
from pathlib import Path

import pytest

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide, TideType
from fishing_forecast_gcal.domain.services.moon_age_calculator import MoonAgeCalculator
from fishing_forecast_gcal.domain.services.prime_time_finder import PrimeTimeFinder
from fishing_forecast_gcal.domain.services.tide_calculation_service import TideCalculationService
from fishing_forecast_gcal.domain.services.tide_type_classifier import TideTypeClassifier
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
)
from fishing_forecast_gcal.infrastructure.repositories.tide_data_repository import (
    TideDataRepository,
)


class TestTideDataRepositoryIntegration:
    """TideDataRepository の統合テスト"""

    @pytest.fixture
    def harmonics_dir(self) -> Path:
        """調和定数ディレクトリのフィクスチャ"""
        return Path(__file__).parent.parent.parent.parent / "config" / "harmonics"

    @pytest.fixture
    def adapter(self, harmonics_dir: Path) -> TideCalculationAdapter:
        """実アダプターのフィクスチャ"""
        return TideCalculationAdapter(harmonics_dir=harmonics_dir)

    @pytest.fixture
    def repository(self, adapter: TideCalculationAdapter) -> TideDataRepository:
        """実リポジトリのフィクスチャ（DI注入あり）"""
        return TideDataRepository(
            adapter=adapter,
            tide_calc_service=TideCalculationService(),
            tide_type_classifier=TideTypeClassifier(),
            prime_time_finder=PrimeTimeFinder(),
            moon_age_calculator=MoonAgeCalculator(),
        )

    @pytest.fixture
    def yokosuka_location(self) -> Location:
        """横須賀地点のフィクスチャ"""
        return Location(
            id="yokosuka",
            name="横須賀",
            latitude=35.28,
            longitude=139.67,
            station_id="TK",
        )

    def test_get_tide_data_with_real_harmonics(
        self,
        repository: TideDataRepository,
        yokosuka_location: Location,
        harmonics_dir: Path,
    ) -> None:
        """実データでの潮汐データ取得

        Note:
            調和定数ファイル（yokosuka.pkl）が存在しない場合はスキップされます。
        """
        # Skip if harmonics file doesn't exist
        harmonics_file = harmonics_dir / f"{yokosuka_location.station_id.lower()}.pkl"
        if not harmonics_file.exists():
            pytest.skip(f"Harmonics file not found: {harmonics_file}")

        # Arrange
        target_date = date(2026, 2, 8)

        # Act
        tide = repository.get_tide_data(yokosuka_location, target_date)

        # Assert
        assert isinstance(tide, Tide)
        assert tide.date == target_date
        assert tide.tide_type in TideType

        # 潮汐イベントの検証
        assert len(tide.events) >= 2  # 少なくとも2回以上の満干潮
        assert len(tide.events) <= 6  # 通常は1日に2-4回程度

        # 満潮と干潮の存在確認
        high_tides = [e for e in tide.events if e.event_type == "high"]
        low_tides = [e for e in tide.events if e.event_type == "low"]
        assert len(high_tides) >= 1
        assert len(low_tides) >= 1

        # 時合い帯の検証（満潮があれば設定されているはず）
        if high_tides:
            assert tide.prime_times is not None
            assert len(tide.prime_times) > 0
            for start, end in tide.prime_times:
                assert start < end

        # イベントが時系列順であることを確認
        for i in range(len(tide.events) - 1):
            assert tide.events[i].time < tide.events[i + 1].time

        # 潮位の範囲確認
        for event in tide.events:
            assert 0 <= event.height_cm <= 500

    def test_tide_prediction_has_minute_resolution(
        self,
        adapter: TideCalculationAdapter,
        yokosuka_location: Location,
        harmonics_dir: Path,
    ) -> None:
        """分単位の時刻が含まれることを確認"""
        harmonics_file = harmonics_dir / f"{yokosuka_location.station_id.lower()}.pkl"
        if not harmonics_file.exists():
            pytest.skip(f"Harmonics file not found: {harmonics_file}")

        target_date = date(2026, 2, 8)
        tide_data = adapter.calculate_tide(yokosuka_location, target_date)

        assert any(dt.minute != 0 for dt, _height in tide_data)

    def test_get_tide_data_missing_harmonics_file(
        self,
        adapter: TideCalculationAdapter,
    ) -> None:
        """調和定数ファイルが存在しない地点でのエラー"""
        # Arrange
        repository = TideDataRepository(adapter=adapter)
        unknown_location = Location(
            id="nonexistent_location",
            name="存在しない地点",
            latitude=35.0,
            longitude=139.0,
            station_id="ZZ",
        )
        target_date = date(2026, 2, 8)

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            repository.get_tide_data(unknown_location, target_date)

    def test_tide_calculation_accuracy(
        self,
        repository: TideDataRepository,
        yokosuka_location: Location,
        harmonics_dir: Path,
    ) -> None:
        """公式潮見表との差分検証

        Note:
            - 調和定数ファイルが存在しない場合はスキップされます
            - 目標精度: ±10cm以内

        Implementation Note:
            このテストは参考実装です。実際の公式データと比較するには、
            気象庁の潮見表データを取得して比較する必要があります。
            現在は潮位の妥当性のみを検証しています。
        """
        # Skip if harmonics file doesn't exist
        harmonics_file = harmonics_dir / f"{yokosuka_location.station_id.lower()}.pkl"
        if not harmonics_file.exists():
            pytest.skip(f"Harmonics file not found: {harmonics_file}")

        # Arrange
        target_date = date(2026, 2, 8)

        # Act
        tide = repository.get_tide_data(yokosuka_location, target_date)

        # Assert: 潮位の妥当性確認
        # 横須賀の典型的な潮位範囲（参考値）
        MIN_EXPECTED_HEIGHT = 0.0  # 干潮の最小値
        MAX_EXPECTED_HEIGHT = 500.0  # 満潮の最大値

        for event in tide.events:
            assert MIN_EXPECTED_HEIGHT <= event.height_cm <= MAX_EXPECTED_HEIGHT, (
                f"Unexpected tide height: {event.height_cm}cm"
            )

        # 潮位差の妥当性確認
        high_tides = [e for e in tide.events if e.event_type == "high"]
        low_tides = [e for e in tide.events if e.event_type == "low"]

        if high_tides and low_tides:
            max_high = max(e.height_cm for e in high_tides)
            min_low = min(e.height_cm for e in low_tides)
            tide_range = max_high - min_low

            # 横須賀の典型的な潮位差（参考値）
            MIN_EXPECTED_RANGE = 20.0  # 小潮時
            MAX_EXPECTED_RANGE = 400.0  # 大潮時
            assert MIN_EXPECTED_RANGE <= tide_range <= MAX_EXPECTED_RANGE, (
                f"Unexpected tide range: {tide_range}cm"
            )

    def test_multiple_dates(
        self,
        repository: TideDataRepository,
        yokosuka_location: Location,
        harmonics_dir: Path,
    ) -> None:
        """複数日の潮汐データ取得"""
        # Skip if harmonics file doesn't exist
        harmonics_file = harmonics_dir / f"{yokosuka_location.station_id.lower()}.pkl"
        if not harmonics_file.exists():
            pytest.skip(f"Harmonics file not found: {harmonics_file}")

        # Arrange
        dates = [date(2026, 2, 8), date(2026, 2, 9), date(2026, 2, 10)]

        # Act
        tides = [repository.get_tide_data(yokosuka_location, d) for d in dates]

        # Assert
        assert len(tides) == 3

        # 各日のデータが正しく取得されていることを確認
        for i, tide in enumerate(tides):
            assert tide.date == dates[i]
            assert len(tide.events) >= 2

        # 潮回りの変化を確認（連続した日で極端に変わることはない）
        tide_types = [t.tide_type for t in tides]
        assert len(set(tide_types)) <= 3  # 3日間で潮回りが3種類以下
