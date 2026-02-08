"""天文潮同期のユースケース

このモジュールは天文潮の同期処理をオーケストレーションします。
潮汐データ取得からカレンダーイベント作成までの一連の流れを統括します。
"""

import logging
from datetime import date

from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide
from fishing_forecast_gcal.domain.repositories.calendar_repository import ICalendarRepository
from fishing_forecast_gcal.domain.repositories.tide_data_repository import ITideDataRepository

logger = logging.getLogger(__name__)


class SyncTideUseCase:
    """天文潮同期のユースケース

    指定された地点・日付の潮汐情報を取得し、
    Google カレンダーにイベントを作成/更新します。

    Attributes:
        _tide_repo: 潮汐データリポジトリ
        _calendar_repo: カレンダーリポジトリ
    """

    def __init__(
        self,
        tide_repo: ITideDataRepository,
        calendar_repo: ICalendarRepository,
    ) -> None:
        """初期化

        Args:
            tide_repo: 潮汐データリポジトリ（依存性注入）
            calendar_repo: カレンダーリポジトリ（依存性注入）
        """
        self._tide_repo = tide_repo
        self._calendar_repo = calendar_repo

    def execute(
        self,
        location: Location,
        target_date: date,
    ) -> None:
        """天文潮を同期

        Args:
            location: 対象地点
            target_date: 対象日

        Raises:
            RuntimeError: 潮汐データ取得またはカレンダー更新に失敗した場合
        """
        logger.info(f"Syncing tide for {location.name} on {target_date}")

        try:
            # 1. 潮汐データ取得
            tide = self._tide_repo.get_tide_data(location, target_date)
            logger.debug(f"Tide data retrieved: {tide.tide_type.value}")

            # 2. イベントID生成（ドメインロジック）
            event_id = CalendarEvent.generate_event_id(location.id, target_date)

            # 3. イベント本文生成
            tide_section = self._format_tide_section(tide)

            # 4. 既存イベント取得
            existing_event = self._calendar_repo.get_event(event_id)

            # 5. 既存の[NOTES]を保持
            existing_notes = None
            if existing_event:
                existing_notes = existing_event.extract_section("NOTES")
                logger.debug("Existing event found, preserving [NOTES] section")

            # 6. イベント本文を構築
            description = self._build_description(tide_section, existing_notes)

            # 7. CalendarEvent作成
            event = CalendarEvent(
                event_id=event_id,
                title=f"{tide.tide_type.to_emoji()}{location.name} ({tide.tide_type.value})",
                description=description,
                date=target_date,
                location_id=location.id,
            )

            # 8. カレンダーに登録
            self._calendar_repo.upsert_event(event)
            logger.info(f"Event upserted successfully: {event_id}")

        except Exception as e:
            logger.error(f"Failed to sync tide: {e}")
            raise RuntimeError(f"Failed to sync tide for {location.name} on {target_date}") from e

    @staticmethod
    def _format_tide_section(tide: Tide) -> str:
        """[TIDE]セクションの生成

        Args:
            tide: 潮汐データ

        Returns:
            [TIDE]セクションの文字列
        """
        lines = []

        # 満潮のリスト
        high_tides = [e for e in tide.events if e.event_type == "high"]
        if high_tides:
            high_times = ", ".join(
                [f"{e.time.strftime('%H:%M')} ({int(e.height_cm)}cm)" for e in high_tides]
            )
            lines.append(f"- 満潮: {high_times}")

        # 干潮のリスト
        low_tides = [e for e in tide.events if e.event_type == "low"]
        if low_tides:
            low_times = ", ".join(
                [f"{e.time.strftime('%H:%M')} ({int(e.height_cm)}cm)" for e in low_tides]
            )
            lines.append(f"- 干潮: {low_times}")

        # 時合い帯
        if tide.prime_time_start and tide.prime_time_end:
            prime_time = (
                f"{tide.prime_time_start.strftime('%H:%M')}-{tide.prime_time_end.strftime('%H:%M')}"
            )
            lines.append(f"- 時合い: {prime_time}")

        return "\n".join(lines)

    @staticmethod
    def _build_description(tide_section: str, existing_notes: str | None) -> str:
        """イベント本文を構築

        Args:
            tide_section: [TIDE]セクションの内容
            existing_notes: 既存の[NOTES]セクション（存在する場合）

        Returns:
            完全なイベント本文
        """
        # 絵文字凡例を先頭に追加
        emoji_legend = "🔴大潮 🟠中潮 🔵小潮 ⚪長潮 🟢若潮"
        sections = [emoji_legend, f"\n[TIDE]\n{tide_section}", "\n[FORECAST]\n（フェーズ2で追加予定）"]

        if existing_notes:
            sections.append(f"\n[NOTES]\n{existing_notes}")
        else:
            sections.append("\n[NOTES]\n（ユーザー手動追記欄）")

        return "\n".join(sections)
