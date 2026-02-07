"""時合い帯特定サービス

満潮前後の時合い帯を計算するドメインサービス。
"""

import logging
from datetime import datetime, timedelta

from fishing_forecast_gcal.domain.models.tide import TideEvent

logger = logging.getLogger(__name__)


class PrimeTimeFinder:
    """時合い帯特定サービス

    満潮時刻を基準に、前後2時間の時合い帯を計算します。
    """

    # 時合い帯の時間幅（満潮前後）
    PRIME_TIME_HOURS = 2

    def find(self, events: list[TideEvent]) -> tuple[datetime, datetime] | None:
        """満潮前後の時合い帯を計算

        Args:
            events: 満干潮のリスト（時系列順）

        Returns:
            (開始時刻, 終了時刻) または None（満潮がない場合）

        Note:
            - 複数の満潮がある場合は、最初の満潮を基準とする
            - 時合い帯は満潮時刻の±2時間
            - 日付を跨ぐ場合も正しく計算される
        """
        # 満潮を抽出
        high_tides = [e for e in events if e.event_type == "high"]

        if not high_tides:
            logger.debug("No high tide found in events")
            return None

        # 最初の満潮を基準とする
        first_high_tide = high_tides[0]
        high_tide_time = first_high_tide.time

        logger.debug(f"Using first high tide at {high_tide_time} for prime time calculation")

        # 時合い帯を計算（±2時間）
        prime_time_start = high_tide_time - timedelta(hours=self.PRIME_TIME_HOURS)
        prime_time_end = high_tide_time + timedelta(hours=self.PRIME_TIME_HOURS)

        return (prime_time_start, prime_time_end)
