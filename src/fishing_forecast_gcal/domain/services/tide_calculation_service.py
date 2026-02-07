"""潮汐計算サービス

連続的な時系列潮位データから満潮・干潮を検出するドメインサービス。
"""

import logging
from datetime import datetime
from typing import Literal

from fishing_forecast_gcal.domain.models.tide import TideEvent

logger = logging.getLogger(__name__)


class TideCalculationService:
    """潮汐計算サービス

    時系列の潮位データから満潮（極大値）・干潮（極小値）を検出します。
    """

    # 潮位の有効範囲（cm単位）
    MIN_HEIGHT_CM = 0.0
    MAX_HEIGHT_CM = 500.0

    def extract_high_low_tides(self, data: list[tuple[datetime, float]]) -> list[TideEvent]:
        """時系列潮位データから満干潮を抽出

        Args:
            data: (時刻, 潮位cm) のタプルのリスト（時系列順）

        Returns:
            満干潮のリスト（時系列順）

        Note:
            - データが3点未満の場合は空リストを返す
            - 極大値は満潮（"high"）、極小値は干潮（"low"）として分類
            - 潮位が有効範囲外の極値はスキップ
        """
        # データ不足チェック
        if len(data) < 3:
            logger.debug(f"Insufficient data points: {len(data)} (minimum 3 required)")
            return []

        events: list[TideEvent] = []

        # 各点について前後の点と比較し、極値を検出
        for i in range(1, len(data) - 1):
            _prev_time, prev_height = data[i - 1]
            curr_time, curr_height = data[i]
            _next_time, next_height = data[i + 1]

            # 極大値（満潮）の検出
            if prev_height < curr_height > next_height:
                event_type: Literal["high", "low"] = "high"
                self._add_event_if_valid(events, curr_time, curr_height, event_type)

            # 極小値（干潮）の検出
            elif prev_height > curr_height < next_height:
                event_type = "low"
                self._add_event_if_valid(events, curr_time, curr_height, event_type)

        return events

    def _add_event_if_valid(
        self,
        events: list[TideEvent],
        time: datetime,
        height_cm: float,
        event_type: Literal["high", "low"],
    ) -> None:
        """潮位が有効範囲内であれば TideEvent を追加

        Args:
            events: イベントリスト（追加先）
            time: 時刻
            height_cm: 潮位（cm）
            event_type: イベントタイプ（"high" or "low"）
        """
        # 潮位の範囲チェック
        if not (self.MIN_HEIGHT_CM <= height_cm <= self.MAX_HEIGHT_CM):
            logger.warning(
                f"Out of range tide height: {height_cm}cm at {time} "
                f"(valid range: {self.MIN_HEIGHT_CM}-{self.MAX_HEIGHT_CM}cm). Skipping."
            )
            return

        # TideEvent を作成して追加
        event = TideEvent(time=time, height_cm=height_cm, event_type=event_type)
        events.append(event)
