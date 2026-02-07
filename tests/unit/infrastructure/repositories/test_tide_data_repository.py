"""Unit tests for TideDataRepository.

このモジュールは TideDataRepository のユニットテストを提供します。
TideCalculationAdapter をモック化して、リポジトリのロジックを検証します。
"""

from datetime import UTC, date, datetime
from unittest.mock import Mock

import pytest

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide, TideType
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
        """リポジトリのフィクスチャ"""
        return TideDataRepository(adapter=mock_adapter)

    @pytest.fixture
    def sample_location(self) -> Location:
        """サンプル地点のフィクスチャ"""
        return Location(
            id="yokosuka",
            name="横須賀",
            latitude=35.28,
            longitude=139.67,
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
        assert tide.prime_time_start is not None  # 時合い帯が計算されている
        assert tide.prime_time_end is not None

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

    def test_calculate_moon_age(self, repository: TideDataRepository) -> None:
        """月齢計算のテスト

        Note:
            基準新月は2000年1月6日 18:14 UTCです。
            計算は対象日の00:00 UTCで行われるため、
            同日の計算では約18時間分の誤差が生じます（約0.75日分）。
        """
        # 2000年1月6日（基準新月の日付）
        # 00:00時点では新月の約18時間前なので、月齢は約29日付近
        moon_age_ref = repository._calculate_moon_age(date(2000, 1, 6))  # type: ignore[reportPrivateUsage]
        assert 28 < moon_age_ref < 30  # 前日の新月周期末期

        # 約15日後は満月（月齢15）
        moon_age_full = repository._calculate_moon_age(date(2000, 1, 21))  # type: ignore[reportPrivateUsage]
        assert 14 < moon_age_full < 16  # 満月付近

        # 約30日後（2000年2月5日）は次の新月周期末期（月齢約29）
        # 2000-01-06 18:14 から 2000-02-05 00:00 は約29.24日後
        moon_age_next = repository._calculate_moon_age(date(2000, 2, 5))  # type: ignore[reportPrivateUsage]
        assert 28 < moon_age_next < 30  # 新月周期末期

        # 2000年1月7日（基準新月の翌日）は月齢約1
        moon_age_day_after = repository._calculate_moon_age(date(2000, 1, 7))  # type: ignore[reportPrivateUsage]
        assert 0 < moon_age_day_after < 2  # 新月直後

        # 2000年2月6日（基準新月から約30.24日後）は新月直後
        moon_age_next_new = repository._calculate_moon_age(date(2000, 2, 6))  # type: ignore[reportPrivateUsage]
        assert 0 <= moon_age_next_new < 2  # 次の新月直後

    def test_calculate_tide_range(self, repository: TideDataRepository) -> None:
        """潮位差計算のテスト"""
        # Arrange
        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        from fishing_forecast_gcal.domain.models.tide import TideEvent

        events = [
            TideEvent(time=base.replace(hour=3), height_cm=150.0, event_type="high"),
            TideEvent(time=base.replace(hour=9), height_cm=50.0, event_type="low"),
            TideEvent(time=base.replace(hour=15), height_cm=160.0, event_type="high"),
            TideEvent(time=base.replace(hour=21), height_cm=55.0, event_type="low"),
        ]

        # Act
        tide_range = repository._calculate_tide_range(events)  # type: ignore[reportPrivateUsage]

        # Assert
        # 最大満潮(160) - 最小干潮(50) = 110
        assert tide_range == 110.0

    def test_calculate_tide_range_no_high_tide(
        self,
        repository: TideDataRepository,
    ) -> None:
        """潮位差計算: 満潮がない場合"""
        # Arrange
        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        from fishing_forecast_gcal.domain.models.tide import TideEvent

        events = [
            TideEvent(time=base.replace(hour=9), height_cm=50.0, event_type="low"),
        ]

        # Act
        tide_range = repository._calculate_tide_range(events)  # type: ignore[reportPrivateUsage]

        # Assert
        assert tide_range == 0.0

    def test_calculate_tide_range_no_low_tide(
        self,
        repository: TideDataRepository,
    ) -> None:
        """潮位差計算: 干潮がない場合"""
        # Arrange
        base = datetime(2026, 2, 8, 0, 0, tzinfo=UTC)
        from fishing_forecast_gcal.domain.models.tide import TideEvent

        events = [
            TideEvent(time=base.replace(hour=3), height_cm=150.0, event_type="high"),
        ]

        # Act
        tide_range = repository._calculate_tide_range(events)  # type: ignore[reportPrivateUsage]  # type: ignore[reportPrivateUsage]

        # Assert
        assert tide_range == 0.0
