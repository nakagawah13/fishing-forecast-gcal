"""Cleanup old Drive images use case.

Google Drive 上の古いタイドグラフ画像を削除するユースケースです。
保持期間を超えた画像ファイルを専用フォルダ内から安全に削除します。
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from fishing_forecast_gcal.infrastructure.clients.google_drive_client import (
    GoogleDriveClient,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CleanupResult:
    """Result of cleanup-images operation.

    クリーンアップ操作の結果を格納します。

    Attributes:
        total_found: Total files found in folder (フォルダ内の総ファイル数)
        total_expired: Total files exceeding retention period (保持期間超過ファイル数)
        total_deleted: Total files successfully deleted (削除成功件数)
        total_failed: Total files that failed to delete (削除失敗件数)
    """

    total_found: int
    total_expired: int
    total_deleted: int
    total_failed: int


class CleanupDriveImagesUseCase:
    """Cleanup old Drive images use case.

    Google Drive 専用フォルダ内の古いタイドグラフ画像を削除します。
    保持期間（retention_days）を超えたファイルのみ対象とします。

    Attributes:
        _drive_client: Google Drive client (Google Drive クライアント)
    """

    def __init__(self, drive_client: GoogleDriveClient) -> None:
        """Initialize with Google Drive client.

        Args:
            drive_client: Google Drive client instance (依存性注入)
        """
        self._drive_client = drive_client

    def execute(
        self,
        folder_name: str,
        retention_days: int,
        *,
        dry_run: bool = False,
    ) -> CleanupResult:
        """Execute cleanup operation.

        指定フォルダ内で保持期間を超えたファイルを削除します。

        Args:
            folder_name: Drive folder name to clean up (対象フォルダ名)
            retention_days: Number of days to retain files (保持日数)
            dry_run: If True, only count without deleting (削除せず件数のみ返す)

        Returns:
            CleanupResult with counts of found, expired, deleted, and failed files
        """
        logger.info(
            "Cleaning up Drive images in '%s' (retention: %d days)%s",
            folder_name,
            retention_days,
            " [DRY-RUN]" if dry_run else "",
        )

        # 1. Get folder ID
        folder_id = self._drive_client.get_or_create_folder(folder_name)
        logger.info("Target folder ID: %s", folder_id)

        # 2. List all files in folder
        files = self._drive_client.list_files(folder_id=folder_id)
        total_found = len(files)
        logger.info("Found %d file(s) in folder", total_found)

        if total_found == 0:
            return CleanupResult(total_found=0, total_expired=0, total_deleted=0, total_failed=0)

        # 3. Filter expired files
        now = datetime.now(tz=UTC)
        expired_files = []

        for file_info in files:
            created_time_str = file_info.get("createdTime", "")
            if not created_time_str:
                logger.warning(
                    "File '%s' (%s) has no createdTime, skipping",
                    file_info.get("name", "unknown"),
                    file_info.get("id", "unknown"),
                )
                continue

            created_time = datetime.fromisoformat(created_time_str.replace("Z", "+00:00"))
            age_days = (now - created_time).days

            if age_days > retention_days:
                expired_files.append(file_info)
                logger.info(
                    "  Expired: %s (age: %d days, created: %s)",
                    file_info.get("name", "unknown"),
                    age_days,
                    created_time_str,
                )

        total_expired = len(expired_files)
        logger.info("%d file(s) exceed retention period of %d days", total_expired, retention_days)

        if total_expired == 0:
            return CleanupResult(
                total_found=total_found, total_expired=0, total_deleted=0, total_failed=0
            )

        if dry_run:
            logger.info("[DRY-RUN] Would delete %d file(s)", total_expired)
            return CleanupResult(
                total_found=total_found,
                total_expired=total_expired,
                total_deleted=0,
                total_failed=0,
            )

        # 4. Delete expired files
        total_deleted = 0
        total_failed = 0

        for file_info in expired_files:
            file_id = file_info["id"]
            file_name = file_info.get("name", "unknown")

            try:
                deleted = self._drive_client.delete_file(file_id)
                if deleted:
                    total_deleted += 1
                    logger.debug("Deleted: %s (%s)", file_name, file_id)
                else:
                    # Not found counts as success (idempotent)
                    total_deleted += 1
                    logger.warning("File already deleted: %s (%s)", file_name, file_id)
            except Exception as e:
                total_failed += 1
                logger.error("Failed to delete %s (%s): %s", file_name, file_id, e)

        logger.info(
            "Cleanup completed: %d found, %d expired, %d deleted, %d failed",
            total_found,
            total_expired,
            total_deleted,
            total_failed,
        )

        return CleanupResult(
            total_found=total_found,
            total_expired=total_expired,
            total_deleted=total_deleted,
            total_failed=total_failed,
        )
