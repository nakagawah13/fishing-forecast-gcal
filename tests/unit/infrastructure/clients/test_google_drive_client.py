"""Unit tests for GoogleDriveClient.

Google Drive API の呼び出しをモック化して、クライアントのロジックを検証する。
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from fishing_forecast_gcal.infrastructure.clients.google_auth import SCOPES
from fishing_forecast_gcal.infrastructure.clients.google_drive_client import (
    DEFAULT_FOLDER_NAME,
    GoogleDriveClient,
)

_DRIVE_MODULE = "fishing_forecast_gcal.infrastructure.clients.google_drive_client"


class TestGoogleDriveClient:
    """GoogleDriveClient のユニットテスト"""

    @pytest.fixture
    def mock_credentials_path(self, tmp_path: Path) -> Path:
        """モック認証情報パスのフィクスチャ"""
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{"installed": {"client_id": "test"}}')
        return creds_path

    @pytest.fixture
    def mock_token_path(self, tmp_path: Path) -> Path:
        """モックトークンパスのフィクスチャ"""
        return tmp_path / "token.json"

    @pytest.fixture
    def client(self, mock_credentials_path: Path, mock_token_path: Path) -> GoogleDriveClient:
        """クライアントのフィクスチャ"""
        return GoogleDriveClient(
            credentials_path=str(mock_credentials_path),
            token_path=str(mock_token_path),
        )

    @pytest.fixture
    def authenticated_client(self, client: GoogleDriveClient) -> GoogleDriveClient:
        """認証済みクライアントのフィクスチャ"""
        mock_service = MagicMock()
        client._service = mock_service  # pyright: ignore[reportPrivateUsage]
        return client


class TestAuthentication(TestGoogleDriveClient):
    """認証関連のテスト"""

    def test_authenticate_delegates_to_google_auth(self, client: GoogleDriveClient) -> None:
        """認証が google_auth.authenticate に委譲される."""
        with (
            patch(f"{_DRIVE_MODULE}._authenticate") as mock_auth,
            patch(f"{_DRIVE_MODULE}.build") as mock_build,
        ):
            mock_creds = MagicMock()
            mock_auth.return_value = mock_creds
            mock_service = MagicMock()
            mock_build.return_value = mock_service

            client.authenticate()

            mock_auth.assert_called_once_with(
                client._credentials_path,  # pyright: ignore[reportPrivateUsage]
                client._token_path,  # pyright: ignore[reportPrivateUsage]
            )
            mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds)
            assert client._service is mock_service  # pyright: ignore[reportPrivateUsage]

    def test_authenticate_missing_credentials_file(self, tmp_path: Path) -> None:
        """認証情報ファイルが存在しない場合はエラー."""
        client = GoogleDriveClient(
            credentials_path=str(tmp_path / "nonexistent.json"),
            token_path=str(tmp_path / "token.json"),
        )

        with pytest.raises(FileNotFoundError, match="Credentials file not found"):
            client.authenticate()

    def test_get_service_without_authentication(self, client: GoogleDriveClient) -> None:
        """認証前に get_service を呼ぶとエラー."""
        with pytest.raises(RuntimeError, match="Drive service not initialized"):
            client.get_service()


class TestUploadFile(TestGoogleDriveClient):
    """upload_file のテスト"""

    def test_upload_file_success(
        self, authenticated_client: GoogleDriveClient, tmp_path: Path
    ) -> None:
        """ファイルアップロードが成功する"""
        # テスト用の一時ファイル作成
        test_file = tmp_path / "test_image.png"
        test_file.write_bytes(b"\x89PNG\r\n")

        service = authenticated_client.get_service()
        service.files().create().execute.return_value = {"id": "file123"}
        service.permissions().create().execute.return_value = {}

        result = authenticated_client.upload_file(test_file)

        assert result["file_id"] == "file123"
        assert result["file_url"] == "https://drive.google.com/file/d/file123/view?usp=drivesdk"

        # files.create が呼ばれたことを確認
        service.files().create.assert_called()
        # permissions.create が呼ばれたことを確認
        service.permissions().create.assert_called()

    def test_upload_file_with_folder_id(
        self, authenticated_client: GoogleDriveClient, tmp_path: Path
    ) -> None:
        """フォルダID指定でアップロードする"""
        test_file = tmp_path / "test_image.png"
        test_file.write_bytes(b"\x89PNG\r\n")

        service = authenticated_client.get_service()
        service.files().create().execute.return_value = {"id": "file456"}
        service.permissions().create().execute.return_value = {}

        result = authenticated_client.upload_file(test_file, folder_id="folder789")

        assert result["file_id"] == "file456"

    def test_upload_file_not_found(
        self, authenticated_client: GoogleDriveClient, tmp_path: Path
    ) -> None:
        """存在しないファイルをアップロードするとエラー"""
        nonexistent_file = tmp_path / "nonexistent.png"

        with pytest.raises(FileNotFoundError, match="File not found"):
            authenticated_client.upload_file(nonexistent_file)

    def test_upload_file_sets_public_permission(
        self, authenticated_client: GoogleDriveClient, tmp_path: Path
    ) -> None:
        """アップロード時に公開読み取り権限が設定される"""
        test_file = tmp_path / "test_image.png"
        test_file.write_bytes(b"\x89PNG\r\n")

        service = authenticated_client.get_service()
        service.files().create().execute.return_value = {"id": "file_abc"}
        service.permissions().create().execute.return_value = {}

        authenticated_client.upload_file(test_file)

        # permissions.create の呼び出しを検証
        service.permissions().create.assert_called_with(
            fileId="file_abc",
            body={"role": "reader", "type": "anyone"},
        )


class TestDeleteFile(TestGoogleDriveClient):
    """delete_file のテスト"""

    def test_delete_file_success(self, authenticated_client: GoogleDriveClient) -> None:
        """ファイル削除が成功する"""
        service = authenticated_client.get_service()
        service.files().delete().execute.return_value = None

        result = authenticated_client.delete_file("file123")

        assert result is True
        service.files().delete.assert_called_with(fileId="file123")

    def test_delete_file_not_found(self, authenticated_client: GoogleDriveClient) -> None:
        """存在しないファイルの削除は False を返す（冪等）"""
        from googleapiclient.errors import HttpError

        service = authenticated_client.get_service()
        mock_resp = Mock()
        mock_resp.status = 404
        service.files().delete().execute.side_effect = HttpError(
            resp=mock_resp, content=b"Not Found"
        )

        result = authenticated_client.delete_file("nonexistent")

        assert result is False

    def test_delete_file_api_error(self, authenticated_client: GoogleDriveClient) -> None:
        """API エラー（404以外）は再送出される"""
        from googleapiclient.errors import HttpError

        service = authenticated_client.get_service()
        mock_resp = Mock()
        mock_resp.status = 500
        service.files().delete().execute.side_effect = HttpError(
            resp=mock_resp, content=b"Internal Server Error"
        )

        with pytest.raises(HttpError):
            authenticated_client.delete_file("file123")


class TestListFiles(TestGoogleDriveClient):
    """list_files のテスト"""

    def test_list_files_basic(self, authenticated_client: GoogleDriveClient) -> None:
        """基本的なファイル一覧取得"""
        service = authenticated_client.get_service()
        service.files().list().execute.return_value = {
            "files": [
                {"id": "f1", "name": "tide_graph_tk_20260215.png"},
                {"id": "f2", "name": "tide_graph_tk_20260216.png"},
            ]
        }

        result = authenticated_client.list_files()

        assert len(result) == 2
        assert result[0]["id"] == "f1"

    def test_list_files_with_folder_id(self, authenticated_client: GoogleDriveClient) -> None:
        """フォルダID指定でファイル一覧を取得"""
        service = authenticated_client.get_service()
        service.files().list().execute.return_value = {"files": []}

        authenticated_client.list_files(folder_id="folder123")

        # list が呼ばれたことを確認
        service.files().list.assert_called()

    def test_list_files_with_query(self, authenticated_client: GoogleDriveClient) -> None:
        """カスタムクエリ付きでファイル一覧を取得"""
        service = authenticated_client.get_service()
        service.files().list().execute.return_value = {"files": []}

        authenticated_client.list_files(query="name contains 'tide_graph'")

        service.files().list.assert_called()

    def test_list_files_empty(self, authenticated_client: GoogleDriveClient) -> None:
        """ファイルが存在しない場合は空リスト"""
        service = authenticated_client.get_service()
        service.files().list().execute.return_value = {"files": []}

        result = authenticated_client.list_files()

        assert result == []

    def test_list_files_pagination(self, authenticated_client: GoogleDriveClient) -> None:
        """ページネーション対応"""
        service = authenticated_client.get_service()

        # 1ページ目: nextPageToken あり
        page1 = {
            "files": [{"id": "f1", "name": "file1.png"}],
            "nextPageToken": "token_page2",
        }
        # 2ページ目: nextPageToken なし
        page2 = {
            "files": [{"id": "f2", "name": "file2.png"}],
        }
        service.files().list().execute.side_effect = [page1, page2]

        result = authenticated_client.list_files()

        assert len(result) == 2
        assert result[0]["id"] == "f1"
        assert result[1]["id"] == "f2"


class TestGetOrCreateFolder(TestGoogleDriveClient):
    """get_or_create_folder のテスト"""

    def test_get_existing_folder(self, authenticated_client: GoogleDriveClient) -> None:
        """既存フォルダを取得する"""
        service = authenticated_client.get_service()
        service.files().list().execute.return_value = {
            "files": [{"id": "existing_folder_id", "name": DEFAULT_FOLDER_NAME}]
        }

        result = authenticated_client.get_or_create_folder()

        assert result == "existing_folder_id"

    def test_create_new_folder(self, authenticated_client: GoogleDriveClient) -> None:
        """フォルダが存在しない場合は新規作成"""
        service = authenticated_client.get_service()
        # フォルダが見つからない
        service.files().list().execute.return_value = {"files": []}
        # 新規作成
        service.files().create().execute.return_value = {"id": "new_folder_id"}

        result = authenticated_client.get_or_create_folder()

        assert result == "new_folder_id"
        # create が呼ばれたことを確認
        service.files().create.assert_called()

    def test_get_or_create_folder_custom_name(
        self, authenticated_client: GoogleDriveClient
    ) -> None:
        """カスタムフォルダ名で取得/作成"""
        service = authenticated_client.get_service()
        service.files().list().execute.return_value = {
            "files": [{"id": "custom_id", "name": "my-custom-folder"}]
        }

        result = authenticated_client.get_or_create_folder("my-custom-folder")

        assert result == "custom_id"


class TestScopes(TestGoogleDriveClient):
    """スコープ定義のテスト"""

    def test_scopes_include_calendar(self) -> None:
        """Calendar スコープが含まれる"""
        assert "https://www.googleapis.com/auth/calendar" in SCOPES

    def test_scopes_include_drive_file(self) -> None:
        """drive.file スコープが含まれる"""
        assert "https://www.googleapis.com/auth/drive.file" in SCOPES

    def test_scopes_count(self) -> None:
        """スコープは2つのみ（最小権限）"""
        assert len(SCOPES) == 2
