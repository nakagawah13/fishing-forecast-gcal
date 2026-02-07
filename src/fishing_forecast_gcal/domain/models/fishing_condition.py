"""釣行条件関連のドメインモデル

このモジュールは気象予報に基づく釣行条件を定義します。
- FishingCondition: 風速、風向、気圧などの予報情報と注意レベル
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class FishingCondition:
    """釣行条件（気象予報情報）

    予報データに基づく釣行可否の判断材料を提供します。

    Attributes:
        wind_speed_mps: 風速（m/s単位、0-50の範囲）
        wind_direction: 風向（例: "北", "北北東", "南西"）
        pressure_hpa: 気圧（hPa単位、900-1100の範囲）
        forecast_time: 予報の基準時刻（timezone aware必須）
        warning_level: 注意レベル（"safe": 安全、"caution": 注意、"danger": 危険）

    Raises:
        ValueError: バリデーションエラー時
    """

    wind_speed_mps: float
    wind_direction: str
    pressure_hpa: float
    forecast_time: datetime
    warning_level: Literal["safe", "caution", "danger"]

    def __post_init__(self) -> None:
        """インスタンス化後のバリデーション"""
        # 風速の範囲チェック
        if not (0 <= self.wind_speed_mps <= 50):
            raise ValueError(
                f"wind_speed_mps must be between 0 and 50, got {self.wind_speed_mps}"
            )

        # 気圧の範囲チェック
        if not (900 <= self.pressure_hpa <= 1100):
            raise ValueError(
                f"pressure_hpa must be between 900 and 1100, got {self.pressure_hpa}"
            )

        # forecast_timeのtimezone確認
        if self.forecast_time.tzinfo is None:
            raise ValueError(
                f"forecast_time must be timezone-aware: {self.forecast_time}"
            )

        # warning_levelの検証（型ヒントで制約されるが念のため）
        if self.warning_level not in ("safe", "caution", "danger"):
            raise ValueError(
                f"warning_level must be 'safe', 'caution' or 'danger', got {self.warning_level}"
            )

    @staticmethod
    def determine_warning_level(wind_speed_mps: float) -> Literal["safe", "caution", "danger"]:
        """風速から注意レベルを自動判定

        Args:
            wind_speed_mps: 風速（m/s）

        Returns:
            注意レベル（"safe", "caution", "danger"）

        Note:
            判定基準:
            - 10m/s以上: danger（釣行中止推奨）
            - 7m/s以上10m/s未満: caution（注意が必要）
            - 7m/s未満: safe（安全）
        """
        if wind_speed_mps >= 10:
            return "danger"
        elif wind_speed_mps >= 7:
            return "caution"
        else:
            return "safe"
