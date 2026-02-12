"""天文潮同期のユースケース

このモジュールは天文潮の同期処理をオーケストレーションします。
潮汐データ取得からカレンダーイベント作成までの一連の流れを統括します。

画像添付が有効な場合:
1. タイドグラフ画像を生成
2. Google Drive にアップロード
3. Calendar イベントに添付
画像添付が失敗しても、イベント同期は継続します（graceful degradation）。
"""

import logging
from datetime import date, timedelta
from pathlib import Path

from fishing_forecast_gcal.domain.models.calendar_event import CalendarEvent
from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.models.tide import Tide, TideType
from fishing_forecast_gcal.domain.repositories.calendar_repository import ICalendarRepository
from fishing_forecast_gcal.domain.repositories.tide_data_repository import ITideDataRepository
from fishing_forecast_gcal.domain.services.tide_graph_service import ITideGraphService
from fishing_forecast_gcal.domain.services.tide_period_analyzer import TidePeriodAnalyzer
from fishing_forecast_gcal.infrastructure.clients.google_drive_client import GoogleDriveClient

logger = logging.getLogger(__name__)


class SyncTideUseCase:
    """天文潮同期のユースケース

    指定された地点・日付の潮汐情報を取得し、
    Google カレンダーにイベントを作成/更新します。

    画像添付が有効な場合は、タイドグラフ画像を生成・アップロード・添付します。

    Attributes:
        _tide_repo: 潮汐データリポジトリ
        _calendar_repo: カレンダーリポジトリ
        _tide_graph_service: タイドグラフ画像生成サービス（オプション）
        _drive_client: Google Drive クライアント（オプション）
        _drive_folder_name: Drive フォルダ名
    """

    def __init__(
        self,
        tide_repo: ITideDataRepository,
        calendar_repo: ICalendarRepository,
        tide_graph_service: ITideGraphService | None = None,
        drive_client: GoogleDriveClient | None = None,
        drive_folder_name: str = "fishing-forecast-tide-graphs",
    ) -> None:
        """初期化

        Args:
            tide_repo: 潮汐データリポジトリ（依存性注入）
            calendar_repo: カレンダーリポジトリ（依存性注入）
            tide_graph_service: タイドグラフ画像生成サービス（オプション）
            drive_client: Google Drive クライアント（オプション）
            drive_folder_name: Drive フォルダ名
        """
        self._tide_repo = tide_repo
        self._calendar_repo = calendar_repo
        self._tide_graph_service = tide_graph_service
        self._drive_client = drive_client
        self._drive_folder_name = drive_folder_name

    @property
    def _tide_graph_enabled(self) -> bool:
        """画像添付が有効かどうか"""
        return self._tide_graph_service is not None and self._drive_client is not None

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
            # 1. 前後数日分の潮汐データを取得（期間判定用）
            date_range = self._get_date_range(target_date, days_before=3, days_after=3)
            tide_data_list: list[tuple[date, Tide]] = []
            for d in date_range:
                try:
                    tide_data = self._tide_repo.get_tide_data(location, d)
                    tide_data_list.append((d, tide_data))
                except Exception as e:
                    # 前後データ取得失敗はログのみ（対象日以外はスキップ）
                    if d == target_date:
                        raise
                    logger.warning(f"Failed to get tide data for {d}: {e}")

            # 2. 対象日のデータを抽出
            tide = next((tide for d, tide in tide_data_list if d == target_date), None)
            if tide is None:
                raise RuntimeError(f"Target date {target_date} not found in retrieved data")
            logger.debug(f"Tide data retrieved: {tide.tide_type.value}")

            # 3. 中央日判定
            is_midpoint = TidePeriodAnalyzer.is_midpoint_day(
                target_date,
                [(d, t.tide_type) for d, t in tide_data_list],
            )
            logger.debug(f"Is midpoint day: {is_midpoint}")

            # 4. イベントID生成（ドメインロジック）
            event_id = CalendarEvent.generate_event_id(location.id, target_date)

            # 5. イベント本文生成（中央日フラグを渡す）
            tide_section = self._format_tide_section(tide, is_midpoint=is_midpoint)

            # 6. 既存イベント取得
            existing_event = self._calendar_repo.get_event(event_id)

            # 7. 既存の[NOTES]を保持
            existing_notes = None
            if existing_event:
                existing_notes = existing_event.extract_section("NOTES")
                logger.debug("Existing event found, preserving [NOTES] section")

            # 8. イベント本文を構築
            description = self._build_description(tide_section, existing_notes)

            # 9. CalendarEvent作成
            event = CalendarEvent(
                event_id=event_id,
                title=f"{tide.tide_type.to_emoji()}{location.name} ({tide.tide_type.value})",
                description=description,
                date=target_date,
                location_id=location.id,
            )

            # 10. タイドグラフ画像の生成・アップロード（有効な場合）
            attachments = self._generate_and_upload_graph(location, target_date, tide)

            # 11. カレンダーに登録（既存イベント情報を渡して重複API呼び出しを回避）
            self._calendar_repo.upsert_event(
                event, existing=existing_event, attachments=attachments
            )
            logger.info(f"Event upserted successfully: {event_id}")

        except Exception as e:
            logger.error(f"Failed to sync tide: {e}")
            raise RuntimeError(f"Failed to sync tide for {location.name} on {target_date}") from e

    def _generate_and_upload_graph(
        self,
        location: Location,
        target_date: date,
        tide: Tide,
    ) -> list[dict[str, str]] | None:
        """タイドグラフ画像を生成・Drive にアップロードし、attachments を返す

        画像添付が無効または失敗した場合は None を返します（graceful degradation）。

        Args:
            location: 対象地点
            target_date: 対象日
            tide: 潮汐データ

        Returns:
            list[dict[str, str]] | None: Calendar attachments（失敗時は None）
        """
        if not self._tide_graph_enabled:
            return None

        assert self._tide_graph_service is not None
        assert self._drive_client is not None

        image_path: Path | None = None
        try:
            # 1. 時系列潮位データを取得
            hourly_heights = self._tide_repo.get_hourly_heights(location, target_date)

            # 2. タイドグラフ画像を生成
            image_path = self._tide_graph_service.generate_graph(
                target_date=target_date,
                hourly_heights=hourly_heights,
                tide_events=tide.events,
                location_name=location.name,
                tide_type=tide.tide_type,
                prime_times=tide.prime_times,
                location_id=location.id,
            )
            logger.info(f"Tide graph generated: {image_path}")

            # 4. Drive フォルダを取得/作成
            folder_id = self._drive_client.get_or_create_folder(self._drive_folder_name)

            # 5. Drive にアップロード（同名ファイルがあれば上書き更新）
            upload_result = self._drive_client.upload_or_update_file(
                file_path=image_path,
                mime_type="image/png",
                folder_id=folder_id,
            )
            logger.info(f"Tide graph uploaded to Drive: {upload_result['file_url']}")

            # 6. attachments を構築
            return [
                {
                    "fileUrl": upload_result["file_url"],
                    "title": image_path.name,
                    "mimeType": "image/png",
                }
            ]

        except Exception as e:
            logger.warning(
                f"Tide graph attachment failed for {location.name} on {target_date}: {e}. "
                "Continuing without image attachment."
            )
            return None

        finally:
            # 7. 一時ファイルを削除
            if image_path and image_path.exists():
                try:
                    image_path.unlink()
                    # 一時ディレクトリも削除（空の場合のみ）
                    parent = image_path.parent
                    if parent.exists() and not any(parent.iterdir()):
                        parent.rmdir()
                    logger.debug(f"Cleaned up temp file: {image_path}")
                except OSError as cleanup_err:
                    logger.warning(f"Failed to clean up temp file {image_path}: {cleanup_err}")

    @staticmethod
    def _get_date_range(target_date: date, days_before: int, days_after: int) -> list[date]:
        """対象日の前後の日付リストを生成

        Args:
            target_date: 基準日
            days_before: 前方日数
            days_after: 後方日数

        Returns:
            日付のリスト（昇順）
        """
        start_date = target_date - timedelta(days=days_before)
        end_date = target_date + timedelta(days=days_after)
        date_range = []
        current = start_date
        while current <= end_date:
            date_range.append(current)
            current += timedelta(days=1)
        return date_range

    @staticmethod
    def _format_tide_section(tide: Tide, is_midpoint: bool = False) -> str:
        """[TIDE]セクションの生成

        Args:
            tide: 潮汐データ
            is_midpoint: 中央日フラグ（Trueの場合、大潮のみマーカーを追加）

        Returns:
            [TIDE]セクションの文字列
        """
        lines = []

        # 中央日マーカーの追加（大潮のみ）
        if is_midpoint and tide.tide_type == TideType.SPRING:
            lines.append("⭐ 中央日")

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

        # 時合い帯（複数対応）
        if tide.prime_times:
            prime_time_strs = [
                f"{pt_start.strftime('%H:%M')}-{pt_end.strftime('%H:%M')}"
                for pt_start, pt_end in tide.prime_times
            ]
            lines.append(f"- 時合い: {', '.join(prime_time_strs)}")

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
        sections = [
            emoji_legend,
            f"\n[TIDE]\n{tide_section}",
            "\n[FORECAST]\n（フェーズ2で追加予定）",
        ]

        if existing_notes:
            sections.append(f"\n[NOTES]\n{existing_notes}")
        else:
            sections.append("\n[NOTES]\n（ユーザー手動追記欄）")

        return "\n".join(sections)
