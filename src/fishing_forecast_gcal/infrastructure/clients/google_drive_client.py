"""Google Drive API client.

Google Drive API のラッパークライアント。
ファイルアップロード、削除、一覧取得、フォルダ管理を提供する。

Authentication is delegated to the shared ``google_auth`` module.
スコープ: ``drive.file``（アプリ作成ファイルのみ、最小権限）
"""

import logging
import pathlib
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from fishing_forecast_gcal.infrastructure.clients.google_auth import (
    authenticate as _authenticate,
)

logger = logging.getLogger(__name__)

# Default folder name for tide graph images on Google Drive
DEFAULT_FOLDER_NAME = "fishing-forecast-tide-graphs"


class GoogleDriveClient:
    """Client for Google Drive API with OAuth2 authentication.

    タイドグラフ画像のアップロード・管理を行う。
    専用フォルダ（デフォルト: ``fishing-forecast-tide-graphs``）にファイルを集約する。
    """

    def __init__(self, credentials_path: str, token_path: str) -> None:
        """Initialize Google Drive client.

        Args:
            credentials_path: Path to OAuth2 credentials JSON file.
                              (OAuth2 認証情報 JSON ファイルのパス)
            token_path: Path to store OAuth2 token JSON file.
                        (OAuth2 トークン JSON ファイルの保存パス)
        """
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._service: Any = None

    def authenticate(self) -> None:
        """Perform OAuth2 authentication and build Drive API service.

        Delegates the OAuth2 flow to the shared ``google_auth`` module,
        then builds the Drive API service with the obtained credentials.

        (OAuth2 認証を共通モジュールに委譲し、Drive API サービスを構築する)

        Raises:
            FileNotFoundError: If credentials file does not exist.
        """
        creds = _authenticate(self._credentials_path, self._token_path)
        self._service = build("drive", "v3", credentials=creds)

    def get_service(self) -> Any:
        """Get authenticated Drive API service.

        Returns:
            Authenticated Google Drive API service instance

        Raises:
            RuntimeError: If authentication has not been performed
        """
        if self._service is None:
            raise RuntimeError("Drive service not initialized. Call authenticate() first.")
        return self._service

    def upload_file(
        self,
        file_path: pathlib.Path,
        mime_type: str = "image/png",
        folder_id: str | None = None,
    ) -> dict[str, str]:
        """Upload a file to Google Drive and set public read permission.

        Args:
            file_path: Local file path to upload
            mime_type: MIME type of the file (default: image/png)
            folder_id: Drive folder ID to upload into (optional)

        Returns:
            Dictionary with keys:
                - ``file_id``: Google Drive file ID
                - ``file_url``: Public URL for Calendar attachments
                  (``https://drive.google.com/file/d/{id}/view?usp=drivesdk``)

        Raises:
            RuntimeError: If Drive service is not initialized
            FileNotFoundError: If local file does not exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        service = self.get_service()

        # Build file metadata
        file_metadata: dict[str, Any] = {"name": file_path.name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(str(file_path), mimetype=mime_type)

        # Upload file
        created_file = (
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        )
        file_id: str = created_file["id"]

        # Set public read permission
        service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        file_url = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
        logger.info("Uploaded %s → %s", file_path.name, file_url)

        return {"file_id": file_id, "file_url": file_url}

    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive (idempotent).

        Args:
            file_id: Google Drive file ID to delete

        Returns:
            True if deleted, False if file did not exist (404)

        Raises:
            RuntimeError: If Drive service is not initialized
        """
        from googleapiclient.errors import HttpError

        service = self.get_service()

        try:
            service.files().delete(fileId=file_id).execute()
            logger.info("Deleted Drive file: %s", file_id)
            return True
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning("Drive file not found (already deleted): %s", file_id)
                return False
            raise

    def list_files(
        self,
        folder_id: str | None = None,
        query: str | None = None,
        page_size: int = 100,
    ) -> list[dict[str, Any]]:
        """List files in Google Drive.

        Args:
            folder_id: Filter by folder ID (optional)
            query: Additional Drive API query string (optional)
            page_size: Number of results per page (default: 100)

        Returns:
            List of file dictionaries with id, name, mimeType, createdTime
        """
        service = self.get_service()

        # Build query parts
        query_parts: list[str] = ["trashed = false"]
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        if query:
            query_parts.append(query)

        q = " and ".join(query_parts)

        all_files: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            kwargs: dict[str, Any] = {
                "q": q,
                "pageSize": page_size,
                "fields": "nextPageToken, files(id, name, mimeType, createdTime)",
            }
            if page_token:
                kwargs["pageToken"] = page_token

            result = service.files().list(**kwargs).execute()
            files = result.get("files", [])
            all_files.extend(files)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_files

    def get_or_create_folder(self, folder_name: str = DEFAULT_FOLDER_NAME) -> str:
        """Get existing folder ID or create a new folder.

        Searches for a folder by exact name match. If not found,
        creates a new folder and returns its ID.

        Args:
            folder_name: Folder name to find or create

        Returns:
            Google Drive folder ID
        """
        service = self.get_service()

        # Search for existing folder
        q = (
            f"name = '{folder_name}' "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )
        result = service.files().list(q=q, fields="files(id, name)", pageSize=1).execute()
        folders = result.get("files", [])

        if folders:
            folder_id: str = folders[0]["id"]
            logger.info("Found existing folder '%s': %s", folder_name, folder_id)
            return folder_id

        # Create new folder
        folder_metadata: dict[str, str] = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder = service.files().create(body=folder_metadata, fields="id").execute()
        folder_id = folder["id"]
        logger.info("Created folder '%s': %s", folder_name, folder_id)
        return folder_id
