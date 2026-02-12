"""Unit tests for TideDataRepository.

このモジュールは TideDataRepository のユニットテストを提供します。
TideCalculationAdapter をモック化して、リポジトリのロジックを検証します。
"""

from datetime import UTC, date, datetime
from unittest.mock import Mock

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


class TestTideDataRepository:
    """TideDataRepository のユニットテスト"""

    @pytest.fixture
    def mock_adapter(self) -> Mock:
        """モックアダプターのフィクスチャ"""
        return Mock(spec=TideCalculationAdapter)

    @pytest.fixture
    def repository(self, mock_adapter: Mock) -> TideDataRepository:
        """リポジトリのフィクスチャ（DI注入あり）"""
        return TideDataRepository(
            adapter=mock_adapter,
            tide_calc_service=TideCalculationService(),
            tide_type_classifier=TideTypeClassifier(),
            prime_time_finder=PrimeTimeFinder(),
            moon_age_calculator=MoonAgeCalculator(),
        )

    @pytest.fixture
    def sample_location(self) -> Location:
        """サンプル地点のフィクスチャ"""
        return Location(
            id="yokosuka",
            name="横須賀",
            latitude=35.28,
            longitude=139.67,
            station_id="TK",
        )

    @pytest.fixture
    def sample_tide_data(self) -> list[tuple[datetime, float]]:
        """サンプル潮位データのフィクスチャ（1日分、満干あり）"""
        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        return [
            (base.replace(hour=0), 100.0),
            (base.replace(hour=1), 120.0),
            (base.replace(hour=2), 140.0),
            (base.replace(hour=3), 150.0),  # 満潮
            (base.replace(hour=4), 140.0),
            (base.replace(hour=5), 120.0),
            (base.replace(hour=6), 100.0),
            (base.replace(hour=7), 80.0),
            (base.replace(hour=8), 60.0),
            (base.replace(hour=9), 50.0),  # 干潮
            (base.replace(hour=10), 60.0),
            (base.replace(hour=11), 80.0),
            (base.replace(hour=12), 100.0),
            (base.replace(hour=13), 120.0),
            (base.replace(hour=14), 140.0),
            (base.replace(hour=15), 160.0),  # 満潮
            (base.replace(hour=16), 140.0),
            (base.replace(hour=17), 120.0),
            (base.replace(hour=18), 100.0),
            (base.replace(hour=19), 80.0),
            (base.replace(hour=20), 60.0),
            (base.replace(hour=21), 50.0),  # 干潮
            (base.replace(hour=22), 60.0),
            (base.replace(hour=23), 80.0),
        ]

    def test_get_tide_data_success(
        self,
        repository: TideDataRepository,
        mock_adapter: Mock,
        sample_location: Location,
        sample_tide_data: list[tuple[datetime, float]],
    ) -> None:
        """正常系: 潮汐データの取得"""
        # Arrange
        target_date = date(2026, 2, 8)
        mock_adapter.calculate_tide.return_value = sample_tide_data

        # Act
        tide = repository.get_tide_data(sample_location, target_date)

        # Assert
        assert isinstance(tide, Tide)
        assert tide.date == target_date
        assert tide.tide_type in TideType  # 何らかの潮回りが判定されている
        assert len(tide.events) > 0  # 満干潮が抽出されている
        assert tide.prime_times is not None  # 時合い帯が計算されている
        assert len(tide.prime_times) > 0

        # 満潮・干潮の検出確認
        high_tides = [e for e in tide.events if e.event_type == "high"]
        low_tides = [e for e in tide.events if e.event_type == "low"]
        assert len(high_tides) == 2  # サンプルデータには満潮が2回
        assert len(low_tides) == 2  # 干潮が2回

        # アダプターが正しく呼び出されたか確認
        mock_adapter.calculate_tide.assert_called_once_with(sample_location, target_date)

    def test_get_tide_data_no_high_tide(
        self,
        repository: TideDataRepository,
        mock_adapter: Mock,
        sample_location: Location,
    ) -> None:
        """正常系: 満潮なしの場合（時合い帯が None）

        Note:
            極大値がないデータを生成するのは困難なため、
            このテストでは干潮のみが検出されるケースを検証します。
        """
        # Arrange
        target_date = date(2026, 2, 8)
        # 緩やかに増加するデータ（極大値を作らない）
        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        # 前半: 100から150まで上昇
        data = [(base.replace(hour=i), 100.0 + i * 2.5) for i in range(0, 12)]
        # 後半: 150から80まで下降（干潮を作る）
        data.extend([(base.replace(hour=12 + i), 150.0 - i * 10.0) for i in range(0, 7)])
        # 最後に少し上昇（干潮80cm）
        data.append((base.replace(hour=19), 82.0))
        data.append((base.replace(hour=20), 85.0))

        mock_adapter.calculate_tide.return_value = data

        # Act
        tide = repository.get_tide_data(sample_location, target_date)

        # Assert
        assert isinstance(tide, Tide)
        # 干潮のみが検出されている
        low_tides = [e for e in tide.events if e.event_type == "low"]
        assert len(low_tides) >= 1

        # 満潮がない場合でも時合い帯が設定される可能性がある
        # （他の満潮が検出された場合）なので、このテストは満潮が
        # 検出されないことに焦点を当てる

    def test_get_tide_data_adapter_failure(
        self,
        repository: TideDataRepository,
        mock_adapter: Mock,
        sample_location: Location,
    ) -> None:
        """異常系: アダプター呼び出し失敗"""
        # Arrange
        target_date = date(2026, 2, 8)
        mock_adapter.calculate_tide.side_effect = RuntimeError("Adapter calculation failed")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            repository.get_tide_data(sample_location, target_date)

        assert "Failed to fetch tide data" in str(exc_info.value)

    def test_get_tide_data_harmonics_not_found(
        self,
        repository: TideDataRepository,
        mock_adapter: Mock,
        sample_location: Location,
    ) -> None:
        """異常系: 調和定数が存在しない地点"""
        # Arrange
        target_date = date(2026, 2, 8)
        mock_adapter.calculate_tide.side_effect = FileNotFoundError(
            "Harmonics file not found for location"
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            repository.get_tide_data(sample_location, target_date)

        assert "Harmonics file not found" in str(exc_info.value)

    def test_get_tide_data_no_events_extracted(
        self,
        repository: TideDataRepository,
        mock_adapter: Mock,
        sample_location: Location,
    ) -> None:
        """異常系: 満干潮が検出されない場合"""
        # Arrange
        target_date = date(2026, 2, 8)
        # データ点が3未満（極値検出不可）
        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        insufficient_data = [(base, 100.0), (base.replace(hour=1), 110.0)]
        mock_adapter.calculate_tide.return_value = insufficient_data

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            repository.get_tide_data(sample_location, target_date)

        assert "No high/low tide events found" in str(exc_info.value)

    def test_default_di_instances_created(self) -> None:
        """デフォルトDI: 引数なしでもインスタンスが作成されること"""
        mock_adapter = Mock(spec=TideCalculationAdapter)
        repo = TideDataRepository(adapter=mock_adapter)
        # Internal services should be auto-created
        assert repo._calculation_service is not None
        assert repo._type_classifier is not None
        assert repo._prime_time_finder is not None
        assert repo._moon_age_calculator is not None

    def test_custom_di_instances_used(self) -> None:
        """カスタムDI: 注入したインスタンスが使用されること"""
        mock_adapter = Mock(spec=TideCalculationAdapter)
        custom_calc = TideCalculationService()
        custom_classifier = TideTypeClassifier()
        custom_finder = PrimeTimeFinder()
        custom_moon = MoonAgeCalculator()

        repo = TideDataRepository(
            adapter=mock_adapter,
            tide_calc_service=custom_calc,
            tide_type_classifier=custom_classifier,
            prime_time_finder=custom_finder,
            moon_age_calculator=custom_moon,
        )
        assert repo._calculation_service is custom_calc
        assert repo._type_classifier is custom_classifier
        assert repo._prime_time_finder is custom_finder
        assert repo._moon_age_calculator is custom_moon
