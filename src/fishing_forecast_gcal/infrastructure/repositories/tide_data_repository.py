"""Tide data repository implementation.

このモジュールは潮汐データリポジトリの実装を提供します。
UTideライブラリアダプターを使用して潮汐データを取得し、
Domainモデルに変換します。
"""

import logging
from datetime import UTC, date, datetime

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide, TideEvent
from fishing_forecast_gcal.domain.repositories.tide_data_repository import ITideDataRepository
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

    # 月の朔望周期（日数）
    MOON_CYCLE_DAYS = 29.53058867

    # 基準新月（2000年1月6日 18:14 UTC）
    REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=UTC)

    def __init__(self, adapter: TideCalculationAdapter) -> None:
        """Initialize tide data repository.

        Args:
            adapter: Tide calculation adapter.
                     (潮汐計算アダプター、依存性注入)
        """
        self._adapter = adapter
        self._calculation_service = TideCalculationService()
        self._type_classifier = TideTypeClassifier()
        self._prime_time_finder = PrimeTimeFinder()

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
            moon_age = self._calculate_moon_age(target_date)
            tide_range = self._calculate_tide_range(events)
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

    def _calculate_moon_age(self, target_date: date) -> float:
        """月齢を計算

        簡易計算式を使用して月齢（0-29.5）を算出します。
        2000年1月6日を基準新月とし、経過日数から計算します。

        Args:
            target_date: 対象日

        Returns:
            float: 月齢（0=新月、15=満月）

        Note:
            実用上十分な精度の簡易実装です。
            専用ライブラリ（ephem等）は使用していません。
        """
        target_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
        days_since_ref = (target_dt - self.REFERENCE_NEW_MOON).total_seconds() / 86400
        moon_age = days_since_ref % self.MOON_CYCLE_DAYS
        return moon_age

    def _calculate_tide_range(self, events: list[TideEvent]) -> float:
        """潮位差を計算

        その日の満潮の最大値と干潮の最小値の差を計算します。

        Args:
            events: 満干潮のリスト

        Returns:
            float: 潮位差（cm）

        Note:
            満潮または干潮がない場合は 0.0 を返します。
        """
        high_tides = [e for e in events if e.event_type == "high"]
        low_tides = [e for e in events if e.event_type == "low"]

        if not high_tides or not low_tides:
            logger.warning("Cannot calculate tide range: missing high or low tide")
            return 0.0

        max_high = max(e.height_cm for e in high_tides)
        min_low = min(e.height_cm for e in low_tides)
        tide_range = max_high - min_low

        logger.debug(
            f"Tide range: {tide_range:.1f}cm (max_high={max_high:.1f}, min_low={min_low:.1f})"
        )
        return tide_range
