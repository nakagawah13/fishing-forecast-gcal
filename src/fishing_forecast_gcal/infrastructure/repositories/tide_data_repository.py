"""Tide data repository implementation.

このモジュールは潮汐データリポジトリの実装を提供します。
UTideライブラリアダプターを使用して潮汐データを取得し、
Domainモデルに変換します。
"""

import logging
from datetime import date

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide
from fishing_forecast_gcal.domain.repositories.tide_data_repository import ITideDataRepository
from fishing_forecast_gcal.domain.services.moon_age_calculator import MoonAgeCalculator
from fishing_forecast_gcal.domain.services.prime_time_finder import PrimeTimeFinder
from fishing_forecast_gcal.domain.services.tide_calculation_service import TideCalculationService
from fishing_forecast_gcal.domain.services.tide_type_classifier import TideTypeClassifier
from fishing_forecast_gcal.infrastructure.adapters.tide_calculation_adapter import (
    TideCalculationAdapter,
)

logger = logging.getLogger(__name__)


class TideDataRepository(ITideDataRepository):
    """Tide data repository implementation.

    TideCalculationAdapterを使用して潮汐データを取得し、
    Domainサービスを使って満干潮・潮回り・時合い帯を計算します。

    Attributes:
        _adapter: Tide calculation adapter for UTide library.
                  (UTideライブラリラッパー)
        _calculation_service: Tide calculation domain service.
                              (満干潮抽出サービス)
        _type_classifier: Tide type classifier domain service.
                          (潮回り判定サービス)
        _prime_time_finder: Prime time finder domain service.
                            (時合い帯計算サービス)
    """

    def __init__(
        self,
        adapter: TideCalculationAdapter,
        tide_calc_service: TideCalculationService | None = None,
        tide_type_classifier: TideTypeClassifier | None = None,
        prime_time_finder: PrimeTimeFinder | None = None,
        moon_age_calculator: MoonAgeCalculator | None = None,
    ) -> None:
        """Initialize tide data repository.

        Args:
            adapter: Tide calculation adapter.
                     (潮汐計算アダプター、依存性注入)
            tide_calc_service: Tide calculation service (DI).
                               Defaults to a new instance.
            tide_type_classifier: Tide type classifier (DI).
                                  Defaults to a new instance.
            prime_time_finder: Prime time finder service (DI).
                               Defaults to a new instance.
            moon_age_calculator: Moon age calculator (DI).
                                 Defaults to a new instance.
        """
        self._adapter = adapter
        self._calculation_service = tide_calc_service or TideCalculationService()
        self._type_classifier = tide_type_classifier or TideTypeClassifier()
        self._prime_time_finder = prime_time_finder or PrimeTimeFinder()
        self._moon_age_calculator = moon_age_calculator or MoonAgeCalculator()

    def get_tide_data(self, location: Location, target_date: date) -> Tide:
        """指定地点・日付の潮汐データを取得

        Args:
            location: 対象地点の情報（緯度・経度を含む）
            target_date: 対象日

        Returns:
            Tide: 潮汐データ（満潮・干潮・潮回りを含む）

        Raises:
            ValueError: 地点または日付が不正な場合
            FileNotFoundError: 地点の調和定数が存在しない場合
            RuntimeError: データ取得に失敗した場合

        Note:
            - 計算精度は実装に依存します（目標: 公式潮見表に対し ±10cm以内）
            - タイムゾーンは UTC として扱われます
        """
        logger.info(f"Fetching tide data for {location.name} on {target_date}")

        try:
            # 1. アダプターから時系列潮位データを取得
            tide_data = self._adapter.calculate_tide(location, target_date)
            logger.debug(f"Received {len(tide_data)} tide data points")

            # 2. 満干潮を抽出
            events = self._calculation_service.extract_high_low_tides(tide_data)
            if not events:
                raise RuntimeError(
                    f"No high/low tide events found for {location.name} on {target_date}"
                )
            logger.debug(f"Extracted {len(events)} tide events")

            # 3. 時合い帯を計算
            prime_time = self._prime_time_finder.find(events)
            prime_time_start = prime_time[0] if prime_time else None
            prime_time_end = prime_time[1] if prime_time else None

            # 4. 潮回りを判定
            moon_age = self._moon_age_calculator.calculate(target_date)
            tide_range = self._calculation_service.calculate_tide_range(events)
            tide_type = self._type_classifier.classify(tide_range, moon_age)
            logger.debug(
                f"Calculated tide_type={tide_type.value}, moon_age={moon_age:.2f}, "
                f"tide_range={tide_range:.1f}cm"
            )

            # 5. Tideモデルを構築
            tide = Tide(
                date=target_date,
                tide_type=tide_type,
                events=events,
                prime_time_start=prime_time_start,
                prime_time_end=prime_time_end,
            )

            logger.info(
                f"Successfully fetched tide data: {tide_type.value}, "
                f"{len(events)} events, prime_time={'set' if prime_time else 'none'}"
            )
            return tide

        except FileNotFoundError as e:
            logger.error(f"Harmonics file not found for {location.name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch tide data for {location.name}: {e}")
            raise RuntimeError(f"Failed to fetch tide data: {e}") from e

    def get_hourly_heights(
        self, location: Location, target_date: date
    ) -> list[tuple[float, float]]:
        """Get hourly heights for graph generation.

        TideCalculationAdapter から時系列潮位データを取得し、
        (hour_float, height_cm) 形式に変換して返します。

        Args:
            location: Target location.
            target_date: Target date.

        Returns:
            list[tuple[float, float]]: (hour 0.0-24.0, height_cm) pairs.

        Raises:
            FileNotFoundError: If harmonic coefficient file is missing.
            RuntimeError: If data retrieval fails.
        """
        logger.info(f"Fetching hourly heights for {location.name} on {target_date}")

        try:
            raw_data = self._adapter.calculate_tide(location, target_date)

            # datetime を hour float (0.0-24.0) に変換し、対象日のデータのみフィルタ
            hourly_heights: list[tuple[float, float]] = []
            for dt, height in raw_data:
                # タイムゾーンを考慮して日付を比較
                local_date = dt.date()
                if local_date == target_date:
                    hour_float = dt.hour + dt.minute / 60.0
                    hourly_heights.append((hour_float, height))

            if not hourly_heights:
                raise RuntimeError(f"No hourly heights found for {location.name} on {target_date}")

            logger.debug(f"Converted {len(hourly_heights)} data points to hourly heights")
            return hourly_heights

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get hourly heights for {location.name}: {e}")
            raise RuntimeError(f"Failed to get hourly heights: {e}") from e
