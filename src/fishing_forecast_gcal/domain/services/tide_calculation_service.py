"""Tide calculation service.

連続的な時系列潮位データから満潮・干潮を検出するドメインサービス。
"""

import logging
from datetime import datetime
from typing import Literal

from fishing_forecast_gcal.domain.models.tide import TideEvent

logger = logging.getLogger(__name__)


class TideCalculationService:
    """Detect high and low tides from time-series data.

    時系列の潮位データから満潮（極大値）・干潮（極小値）を検出します。
    """

    # 潮位の有効範囲（cm単位）
    MIN_HEIGHT_CM = 0.0
    MAX_HEIGHT_CM = 500.0

    def extract_high_low_tides(self, data: list[tuple[datetime, float]]) -> list[TideEvent]:
        """Extract high and low tides from time-series data.

        時系列潮位データから満干潮を抽出します。

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

        prev_sign = self._trend_sign(data[1][1] - data[0][1])
        index = 1

        while index < len(data) - 1:
            curr_height = data[index][1]
            next_height = data[index + 1][1]
            curr_sign = self._trend_sign(next_height - curr_height)

            if curr_sign == 0:
                plateau_start = index
                while (
                    index < len(data) - 1
                    and self._trend_sign(data[index + 1][1] - data[index][1]) == 0
                ):
                    index += 1
                plateau_end = index
                if index >= len(data) - 1:
                    break
                next_sign = self._trend_sign(data[index + 1][1] - data[index][1])

                if prev_sign > 0 and next_sign < 0:
                    midpoint_index = (plateau_start + plateau_end) // 2
                    time, height_cm = data[midpoint_index]
                    self._add_event_if_valid(events, time, height_cm, "high")
                elif prev_sign < 0 and next_sign > 0:
                    midpoint_index = (plateau_start + plateau_end) // 2
                    time, height_cm = data[midpoint_index]
                    self._add_event_if_valid(events, time, height_cm, "low")

                if next_sign != 0:
                    prev_sign = next_sign

                index += 1
                continue

            if prev_sign > 0 and curr_sign < 0:
                time, height_cm = data[index]
                self._add_event_if_valid(events, time, height_cm, "high")
            elif prev_sign < 0 and curr_sign > 0:
                time, height_cm = data[index]
                self._add_event_if_valid(events, time, height_cm, "low")

            prev_sign = curr_sign
            index += 1

        return events

    @staticmethod
    def _trend_sign(delta: float) -> int:
        """Return the sign of a delta value.

        差分の符号を返します。

        Args:
            delta: 連続データ間の差分値

        Returns:
            差分の符号（正なら1、負なら-1、ゼロなら0）
        """
        if delta > 0:
            return 1
        if delta < 0:
            return -1
        return 0

    def _add_event_if_valid(
        self,
        events: list[TideEvent],
        time: datetime,
        height_cm: float,
        event_type: Literal["high", "low"],
    ) -> None:
        """Add a TideEvent when the height is within range.

        潮位が有効範囲内であれば TideEvent を追加します。

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
