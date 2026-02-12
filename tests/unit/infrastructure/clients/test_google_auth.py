"""Unit tests for google_auth module.

共通 OAuth2 認証ヘルパーのユニットテストを提供する。
トークン読み込み、リフレッシュ、新規認証フローを検証する。
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fishing_forecast_gcal.infrastructure.clients.google_auth import (
    SCOPES,
    authenticate,
)

_AUTH_MODULE = "fishing_forecast_gcal.infrastructure.clients.google_auth"


class TestScopes:
    """SCOPES 定数のテスト"""

    def test_scopes_contains_calendar(self) -> None:
        """Calendar API スコープが含まれること."""
        assert "https://www.googleapis.com/auth/calendar" in SCOPES

    def test_scopes_contains_drive_file(self) -> None:
        """Drive file スコープが含まれること."""
        assert "https://www.googleapis.com/auth/drive.file" in SCOPES

    def test_scopes_length(self) -> None:
        """スコープが2つであること."""
        assert len(SCOPES) == 2


class TestAuthenticate:
    """authenticate() 関数のテスト"""

    @pytest.fixture
    def mock_credentials_path(self, tmp_path: Path) -> Path:
        """モック認証情報パスのフィクスチャ."""
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{"installed": {"client_id": "test"}}')
        return creds_path

    @pytest.fixture
    def mock_token_path(self, tmp_path: Path) -> Path:
        """モックトークンパスのフィクスチャ."""
        return tmp_path / "token.json"

    def test_authenticate_with_existing_valid_token(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """既存の有効なトークンで認証する."""
        mock_token_path.write_text(json.dumps({"token": "mock", "refresh_token": "mock_refresh"}))

        with patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls:
            mock_creds = MagicMock()
            mock_creds.valid = True
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            mock_creds_cls.from_authorized_user_file.assert_called_once_with(
                str(mock_token_path), SCOPES
            )
            assert result is mock_creds

    def test_authenticate_refreshes_expired_token(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """期限切れトークンをリフレッシュする."""
        mock_token_path.write_text(json.dumps({"token": "mock", "refresh_token": "mock_refresh"}))

        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.Request") as mock_request,
        ):
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "mock_refresh"
            mock_creds.to_json.return_value = '{"token": "refreshed"}'
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            mock_creds.refresh.assert_called_once_with(mock_request())
            assert result is mock_creds

    def test_authenticate_saves_token_after_refresh(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """リフレッシュ後にトークンが保存される."""
        mock_token_path.write_text(json.dumps({"token": "mock", "refresh_token": "mock_refresh"}))

        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.Request"),
        ):
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "mock_refresh"
            mock_creds.to_json.return_value = '{"token": "refreshed"}'
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            authenticate(str(mock_credentials_path), str(mock_token_path))

            # Token file should be saved
            assert mock_token_path.exists()
            assert mock_token_path.read_text() == '{"token": "refreshed"}'

    def test_authenticate_new_oauth_flow(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """新規 OAuth 認証フローを実行する."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            # No existing token file, from_authorized_user_file not called
            mock_creds_cls.from_authorized_user_file.side_effect = Exception()

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "new"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            mock_flow_cls.from_client_secrets_file.assert_called_once_with(
                str(mock_credentials_path), SCOPES
            )
            mock_flow.run_local_server.assert_called_once_with(port=0)
            assert result is mock_new_creds

    def test_authenticate_raises_when_no_credentials_file(self, tmp_path: Path) -> None:
        """credentials ファイルが存在しない場合に FileNotFoundError."""
        non_existent = tmp_path / "missing_credentials.json"
        token_path = tmp_path / "token.json"

        with pytest.raises(FileNotFoundError, match="Credentials file not found"):
            authenticate(str(non_existent), str(token_path))

    def test_authenticate_creates_token_parent_dir(
        self, mock_credentials_path: Path, tmp_path: Path
    ) -> None:
        """トークンファイルの親ディレクトリが自動作成される."""
        nested_token_path = tmp_path / "subdir" / "deep" / "token.json"

        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            mock_creds_cls.from_authorized_user_file.side_effect = Exception()

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "new"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            authenticate(str(mock_credentials_path), str(nested_token_path))

            assert nested_token_path.exists()
