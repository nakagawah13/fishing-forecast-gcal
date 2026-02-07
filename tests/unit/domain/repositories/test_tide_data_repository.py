"""潮汐データリポジトリインターフェースのテスト

ITideDataRepository の抽象基底クラスとしての振る舞いをテストします。
"""

from datetime import UTC, date, datetime
from typing import override

import pytest

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide, TideEvent, TideType
from fishing_forecast_gcal.domain.repositories.tide_data_repository import (
    ITideDataRepository,
)


class TestITideDataRepositoryAbstract:
    """抽象基底クラスとしての振る舞いをテスト"""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """抽象基底クラスを直接インスタンス化できないことを確認"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ITideDataRepository()  # type: ignore[abstract]

    def test_cannot_instantiate_incomplete_subclass(self) -> None:
        """抽象メソッドを実装していないサブクラスはインスタンス化できないことを確認"""

        class IncompleteRepository(ITideDataRepository):
            """抽象メソッドを実装していない不完全なサブクラス"""

            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteRepository()  # type: ignore[abstract]


class TestITideDataRepositoryMock:
    """Mock実装を使った動作テスト"""

    def test_mock_implementation_works(self) -> None:
        """Mock実装が正しく動作することを確認"""

        class MockTideDataRepository(ITideDataRepository):
            """テスト用のMock実装"""

            @override
            def get_tide_data(self, location: Location, target_date: date) -> Tide:
                """固定値を返すMock実装"""
                return Tide(
                    date=target_date,
                    tide_type=TideType.SPRING,
                    events=[
                        TideEvent(
                            time=datetime(2026, 2, 8, 6, 12, tzinfo=UTC),
                            height_cm=162.0,
                            event_type="high",
                        ),
                        TideEvent(
                            time=datetime(2026, 2, 8, 12, 34, tzinfo=UTC),
                            height_cm=58.0,
                            event_type="low",
                        ),
                    ],
                )

        # Mock実装をインスタンス化
        repository = MockTideDataRepository()

        # 動作確認
        location = Location(id="tokyo_bay", name="東京湾", latitude=35.6, longitude=139.8)
        target_date = date(2026, 2, 8)
        tide = repository.get_tide_data(location, target_date)

        # 検証
        assert tide.date == target_date
        assert tide.tide_type == TideType.SPRING
        assert len(tide.events) == 2
        assert tide.events[0].event_type == "high"
        assert tide.events[0].height_cm == 162.0
        assert tide.events[1].event_type == "low"
        assert tide.events[1].height_cm == 58.0
