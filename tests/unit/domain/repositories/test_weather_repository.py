"""気象予報リポジトリインターフェースのテスト

IWeatherRepository の抽象基底クラスとしての振る舞いをテストします。
"""

from datetime import UTC, date, datetime
from typing import override

import pytest

from fishing_forecast_gcal.domain.models.fishing_condition import FishingCondition
from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.repositories.weather_repository import (
    IWeatherRepository,
)


class TestIWeatherRepositoryAbstract:
    """抽象基底クラスとしての振る舞いをテスト"""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """抽象基底クラスを直接インスタンス化できないことを確認"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IWeatherRepository()  # type: ignore[abstract]

    def test_cannot_instantiate_incomplete_subclass(self) -> None:
        """抽象メソッドを実装していないサブクラスはインスタンス化できないことを確認"""

        class IncompleteRepository(IWeatherRepository):
            """抽象メソッドを実装していない不完全なサブクラス"""

            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteRepository()  # type: ignore[abstract]


class TestIWeatherRepositoryMock:
    """Mock実装を使った動作テスト"""

    def test_mock_implementation_returns_forecast(self) -> None:
        """Mock実装が予報データを返すことを確認"""

        class MockWeatherRepository(IWeatherRepository):
            """テスト用のMock実装（予報あり）"""

            @override
            def get_forecast(
                self, location: Location, target_date: date
            ) -> FishingCondition | None:
                """固定値を返すMock実装"""
                return FishingCondition(
                    wind_speed_mps=5.0,
                    wind_direction="北",
                    pressure_hpa=1012.0,
                    forecast_time=datetime(2026, 2, 8, 9, 0, tzinfo=UTC),
                    warning_level="safe",
                )

        # Mock実装をインスタンス化
        repository = MockWeatherRepository()

        # 動作確認
        location = Location(id="tokyo_bay", name="東京湾", latitude=35.6, longitude=139.8)
        target_date = date(2026, 2, 8)
        condition = repository.get_forecast(location, target_date)

        # 検証
        assert condition is not None
        assert condition.wind_speed_mps == 5.0
        assert condition.wind_direction == "北"
        assert condition.pressure_hpa == 1012.0
        assert condition.warning_level == "safe"

    def test_mock_implementation_returns_none(self) -> None:
        """Mock実装が予報なしの場合にNoneを返すことを確認"""

        class MockWeatherRepositoryNoForecast(IWeatherRepository):
            """テスト用のMock実装（予報なし）"""

            @override
            def get_forecast(
                self, location: Location, target_date: date
            ) -> FishingCondition | None:
                """Noneを返すMock実装（予報が取得できない場合）"""
                return None

        # Mock実装をインスタンス化
        repository = MockWeatherRepositoryNoForecast()

        # 動作確認
        location = Location(id="tokyo_bay", name="東京湾", latitude=35.6, longitude=139.8)
        target_date = date(2026, 2, 8)
        condition = repository.get_forecast(location, target_date)

        # 検証
        assert condition is None
