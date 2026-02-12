"""Moon age calculator domain service.

月齢（月の満ち欠けの日数）を計算するドメインサービス。
潮回り判定（TideTypeClassifier）の入力として使用します。
"""

import logging
from datetime import UTC, date, datetime

logger = logging.getLogger(__name__)


class MoonAgeCalculator:
    """Moon age calculator.

    簡易計算式を使用して月齢（0-29.5）を算出します。
    2000年1月6日を基準新月とし、経過日数から計算します。

    Usage:
        >>> MoonAgeCalculator.calculate(date(2026, 2, 8))
        15.2  # approximate full moon
    """

    # Synodic period of the Moon (days)
    MOON_CYCLE_DAYS = 29.53058867

    # Reference new moon: 2000-01-06 18:14 UTC
    REFERENCE_NEW_MOON = datetime(2000, 1, 6, 18, 14, tzinfo=UTC)

    @staticmethod
    def calculate(target_date: date) -> float:
        """Calculate moon age for the given date.

        Args:
            target_date: Target date to calculate moon age for.

        Returns:
            Moon age in days (0 = new moon, ~15 = full moon).

        Note:
            This is a simplified calculation using a fixed synodic period.
            Accuracy is sufficient for tide type classification but not for
            precise astronomical purposes.
        """
        target_dt = datetime.combine(target_date, datetime.min.time(), tzinfo=UTC)
        days_since_ref = (target_dt - MoonAgeCalculator.REFERENCE_NEW_MOON).total_seconds() / 86400
        moon_age = days_since_ref % MoonAgeCalculator.MOON_CYCLE_DAYS
        return moon_age
