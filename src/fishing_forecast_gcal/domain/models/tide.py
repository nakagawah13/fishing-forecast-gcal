"""潮汐関連のドメインモデル

このモジュールは潮汐に関連するドメインモデルを定義します。
- TideType: 潮回りの種類（大潮、中潮、小潮など）
- TideEvent: 満潮・干潮の1回分のイベント
- Tide: 1日分の潮汐情報
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Literal


class TideType(Enum):
    """潮回りの種類

    天文潮の周期に基づく潮の大きさの分類。
    月齢と関連し、釣行計画の重要な指標となる。
    """

    SPRING = "大潮"  # 満月・新月付近、潮位差が最大
    MODERATE = "中潮"  # 上弦・下弦付近、潮位差が中程度
    NEAP = "小潮"  # 中間期、潮位差が最小
    LONG = "長潮"  # 小潮の翌日、潮の動きが緩慢
    YOUNG = "若潮"  # 長潮の翌日、潮が復活し始める

    def to_emoji(self) -> str:
        """潮回り種別に対応する絵文字を返す

        カレンダーイベントのタイトルや説明文で視認性を高めるために使用します。

        Returns:
            潮回りの種別を表す絵文字（1文字）

        Example:
            >>> TideType.SPRING.to_emoji()
            '🔴'
            >>> TideType.NEAP.to_emoji()
            '🔵'
        """
        emoji_map = {
            TideType.SPRING: "🔴",
            TideType.MODERATE: "🟠",
            TideType.NEAP: "🔵",
            TideType.LONG: "⚪",
            TideType.YOUNG: "🟢",
        }
        return emoji_map[self]


@dataclass(frozen=True)
class TideEvent:
    """満潮・干潮の1回分のイベント

    1日の中で発生する満潮または干潮の情報を表現します。

    Attributes:
        time: 発生時刻（timezone aware必須）
        height_cm: 潮位（cm単位、0-500の範囲）
        event_type: イベントの種類（"high": 満潮、"low": 干潮）

    Raises:
        ValueError: バリデーションエラー時
    """

    time: datetime
    height_cm: float
    event_type: Literal["high", "low"]

    def __post_init__(self) -> None:
        """インスタンス化後のバリデーション"""
        # timezoneの確認
        if self.time.tzinfo is None:
            raise ValueError(f"time must be timezone-aware: {self.time}")

        # 潮位の範囲チェック
        if not (0 <= self.height_cm <= 500):
            raise ValueError(f"height_cm must be between 0 and 500, got {self.height_cm}")

        # event_typeの検証（型ヒントで制約されるが念のため）
        if self.event_type not in ("high", "low"):
            raise ValueError(f"event_type must be 'high' or 'low', got {self.event_type}")


@dataclass(frozen=True)
class Tide:
    """1日分の潮汐情報

    特定の日付における潮汐の全体像（潮回り、満干潮、時合い帯）を表現します。

    Attributes:
        date: 対象日
        tide_type: 潮回り（大潮、中潮など）
        events: 満干潮のリスト（時系列順）
        prime_time_start: 時合い帯開始時刻（満潮の約2時間前）
        prime_time_end: 時合い帯終了時刻（満潮の約2時間後）

    Raises:
        ValueError: バリデーションエラー時
    """

    date: date
    tide_type: TideType
    events: list[TideEvent]
    prime_time_start: datetime | None = None
    prime_time_end: datetime | None = None

    def __post_init__(self) -> None:
        """インスタンス化後のバリデーション"""
        # eventsが空でないこと
        if not self.events:
            raise ValueError("events must not be empty")

        # eventsが時系列順であること
        for i in range(len(self.events) - 1):
            if self.events[i].time >= self.events[i + 1].time:
                raise ValueError(
                    f"events must be in chronological order: "
                    f"{self.events[i].time} >= {self.events[i + 1].time}"
                )

        # prime_timeの整合性チェック（両方nullまたは両方non-null）
        prime_time_set = {self.prime_time_start is not None, self.prime_time_end is not None}
        if len(prime_time_set) > 1:
            raise ValueError("prime_time_start and prime_time_end must be both set or both None")

        # prime_timeが設定されている場合、開始<終了であること
        if self.prime_time_start is not None and self.prime_time_end is not None:
            if self.prime_time_start >= self.prime_time_end:
                raise ValueError(
                    f"prime_time_start must be before prime_time_end: "
                    f"{self.prime_time_start} >= {self.prime_time_end}"
                )
