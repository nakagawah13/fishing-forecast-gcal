"""Unit tests for CleanupDriveImagesUseCase.

CleanupDriveImagesUseCase の単体テストです。
GoogleDriveClient をモック化して削除ロジックを検証します。
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from fishing_forecast_gcal.application.usecases.cleanup_drive_images_usecase import (
    CleanupDriveImagesUseCase,
    CleanupResult,
)
from fishing_forecast_gcal.infrastructure.clients.google_drive_client import (
    GoogleDriveClient,
)


@pytest.fixture
def mock_drive_client() -> MagicMock:
    """Mock GoogleDriveClient instance."""
    return MagicMock(spec=GoogleDriveClient)


@pytest.fixture
def cleanup_usecase(mock_drive_client: MagicMock) -> CleanupDriveImagesUseCase:
    """CleanupDriveImagesUseCase instance with mock client."""
    return CleanupDriveImagesUseCase(drive_client=mock_drive_client)


def _make_file(
    file_id: str,
    name: str,
    created_time: datetime,
) -> dict[str, str]:
    """Helper to create a Drive file dict.

    Args:
        file_id: File ID
        name: File name
        created_time: Creation time (UTC)

    Returns:
        Drive API-like file dictionary
    """
    return {
        "id": file_id,
        "name": name,
        "mimeType": "image/png",
        "createdTime": created_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }


class TestCleanupDriveImagesUseCase:
    """CleanupDriveImagesUseCase tests."""

    def test_execute_deletes_expired_files(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: deletes files exceeding retention period. (正常系: 期限超過ファイルの削除)"""
        now = datetime.now(tz=UTC)

        # 45日前と10日前のファイル。retention=30日 → 45日前のみ削除
        old_file = _make_file(
            "old_id",
            "old_graph.png",
            datetime(now.year, now.month, now.day, tzinfo=UTC).replace(
                year=now.year, month=now.month, day=now.day
            ),
            # 45日前を計算
        )
        # datetime計算をより明確に
        from datetime import timedelta

        old_time = now - timedelta(days=45)
        recent_time = now - timedelta(days=10)

        old_file = _make_file("old_id", "old_graph.png", old_time)
        recent_file = _make_file("recent_id", "recent_graph.png", recent_time)

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [old_file, recent_file]
        mock_drive_client.delete_file.return_value = True

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=2, total_expired=1, total_deleted=1, total_failed=0
        )
        mock_drive_client.delete_file.assert_called_once_with("old_id")

    def test_execute_no_files_in_folder(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: no files to process. (正常系: フォルダが空)"""
        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = []

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=0, total_expired=0, total_deleted=0, total_failed=0
        )
        mock_drive_client.delete_file.assert_not_called()

    def test_execute_no_expired_files(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: all files within retention period. (正常系: 全ファイル保持期間内)"""
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        recent_file_1 = _make_file("id1", "graph1.png", now - timedelta(days=5))
        recent_file_2 = _make_file("id2", "graph2.png", now - timedelta(days=15))

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [recent_file_1, recent_file_2]

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=2, total_expired=0, total_deleted=0, total_failed=0
        )
        mock_drive_client.delete_file.assert_not_called()

    def test_execute_dry_run(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: dry-run does not delete. (正常系: dry-run では削除しない)"""
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        old_file = _make_file("old_id", "old_graph.png", now - timedelta(days=45))

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [old_file]

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
            dry_run=True,
        )

        assert result == CleanupResult(
            total_found=1, total_expired=1, total_deleted=0, total_failed=0
        )
        mock_drive_client.delete_file.assert_not_called()

    def test_execute_delete_failure_counted(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Error: deletion failure is counted in total_failed. (異常系: 削除失敗のカウント)"""
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        old_file_1 = _make_file("id1", "graph1.png", now - timedelta(days=45))
        old_file_2 = _make_file("id2", "graph2.png", now - timedelta(days=60))

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [old_file_1, old_file_2]
        # 1件目は成功、2件目はエラー
        mock_drive_client.delete_file.side_effect = [True, Exception("API error")]

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=2, total_expired=2, total_deleted=1, total_failed=1
        )
        assert mock_drive_client.delete_file.call_count == 2

    def test_execute_all_files_expired(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: all files are expired and deleted. (正常系: 全ファイル期限超過で削除)"""
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        old_files = [
            _make_file(f"id{i}", f"graph{i}.png", now - timedelta(days=40 + i)) for i in range(3)
        ]

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = old_files
        mock_drive_client.delete_file.return_value = True

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=3, total_expired=3, total_deleted=3, total_failed=0
        )
        assert mock_drive_client.delete_file.call_count == 3

    def test_execute_file_already_deleted(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: file not found (404) counts as success. (正常系: 既に削除済みは成功扱い)"""
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        old_file = _make_file("old_id", "old_graph.png", now - timedelta(days=45))

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [old_file]
        mock_drive_client.delete_file.return_value = False  # 404 → False

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=1, total_expired=1, total_deleted=1, total_failed=0
        )

    def test_execute_file_without_created_time(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Edge: file without createdTime is skipped. (境界: createdTimeなしファイルはスキップ)"""
        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [
            {"id": "no_time_id", "name": "no_time.png", "mimeType": "image/png"}
        ]

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=30,
        )

        assert result == CleanupResult(
            total_found=1, total_expired=0, total_deleted=0, total_failed=0
        )
        mock_drive_client.delete_file.assert_not_called()

    def test_execute_custom_retention_days(
        self,
        cleanup_usecase: CleanupDriveImagesUseCase,
        mock_drive_client: MagicMock,
    ) -> None:
        """Normal: custom retention days respected. (正常系: カスタム保持日数)"""
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        # 8日前のファイル。retention=7日 → 削除対象
        file_8_days = _make_file("id1", "graph1.png", now - timedelta(days=8))
        # 5日前のファイル。retention=7日 → 保持
        file_5_days = _make_file("id2", "graph2.png", now - timedelta(days=5))

        mock_drive_client.get_or_create_folder.return_value = "folder_123"
        mock_drive_client.list_files.return_value = [file_8_days, file_5_days]
        mock_drive_client.delete_file.return_value = True

        result = cleanup_usecase.execute(
            folder_name="fishing-forecast-tide-graphs",
            retention_days=7,
        )

        assert result == CleanupResult(
            total_found=2, total_expired=1, total_deleted=1, total_failed=0
        )
        mock_drive_client.delete_file.assert_called_once_with("id1")
