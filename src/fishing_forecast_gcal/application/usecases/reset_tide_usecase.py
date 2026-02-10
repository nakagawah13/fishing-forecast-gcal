"""Reset tide events use case.

登録済みの潮汐カレンダーイベントを安全に削除するユースケースです。
指定された期間・地点のイベントを検索し、一括削除します。
"""

import logging
from dataclasses import dataclass
from datetime import date

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.domain.repositories.calendar_repository import ICalendarRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResetResult:
    """Result of reset-tide operation.

    リセット操作の結果を格納します。

    Attributes:
        total_found: Total events found matching criteria (検索件数)
        total_deleted: Total events successfully deleted (削除件数)
        total_failed: Total events that failed to delete (失敗件数)
    """

    total_found: int
    total_deleted: int
    total_failed: int


class ResetTideUseCase:
    """Reset tide events use case.

    指定された期間・地点の潮汐イベントを検索し、一括削除します。
    dry-run モードでは削除せずに対象件数のみ返します。

    Attributes:
        _calendar_repo: Calendar repository (カレンダーリポジトリ)
    """

    def __init__(self, calendar_repo: ICalendarRepository) -> None:
        """Initialize with calendar repository.

        Args:
            calendar_repo: Calendar repository instance (依存性注入)
        """
        self._calendar_repo = calendar_repo

    def execute(
        self,
        location: Location,
        start_date: date,
        end_date: date,
        dry_run: bool = False,
    ) -> ResetResult:
        """Execute reset-tide operation.

        指定期間・地点のイベントを検索し、削除します。

        Args:
            location: Target location (対象地点)
            start_date: Start date inclusive (開始日)
            end_date: End date inclusive (終了日)
            dry_run: If True, only count without deleting (削除せず件数のみ返す)

        Returns:
            ResetResult with counts of found, deleted, and failed events

        Raises:
            RuntimeError: If event listing or deletion fails
        """
        logger.info(
            "Resetting tide events for %s (%s) from %s to %s%s",
            location.name,
            location.id,
            start_date,
            end_date,
            " [DRY-RUN]" if dry_run else "",
        )

        # 1. List matching events
        events = self._calendar_repo.list_events(start_date, end_date, location.id)
        total_found = len(events)

        logger.info("Found %d event(s) matching criteria", total_found)

        if total_found == 0:
            return ResetResult(total_found=0, total_deleted=0, total_failed=0)

        # Log event details
        for event in events:
            logger.info("  - %s: %s", event.date, event.title)

        if dry_run:
            logger.info("[DRY-RUN] Would delete %d event(s)", total_found)
            return ResetResult(total_found=total_found, total_deleted=0, total_failed=0)

        # 2. Delete events
        total_deleted = 0
        total_failed = 0

        for event in events:
            try:
                deleted = self._calendar_repo.delete_event(event.event_id)
                if deleted:
                    total_deleted += 1
                    logger.debug("Deleted event: %s (%s)", event.event_id, event.date)
                else:
                    logger.warning(
                        "Event already deleted or not found: %s (%s)",
                        event.event_id,
                        event.date,
                    )
                    # Not found counts as success (idempotent)
                    total_deleted += 1
            except Exception as e:
                total_failed += 1
                logger.error("Failed to delete event %s (%s): %s", event.event_id, event.date, e)

        logger.info(
            "Reset completed: %d found, %d deleted, %d failed",
            total_found,
            total_deleted,
            total_failed,
        )

        return ResetResult(
            total_found=total_found,
            total_deleted=total_deleted,
            total_failed=total_failed,
        )
