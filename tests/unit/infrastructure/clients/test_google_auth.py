"""Unit tests for google_auth module.

共通 OAuth2 認証ヘルパーのユニットテストを提供する。
トークン読み込み、リフレッシュ、新規認証フロー、
スコープ不一致ハンドリングを検証する。
"""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from google.auth.exceptions import RefreshError

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
            mock_creds.scopes = set(SCOPES)
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


class TestScopeMismatch:
    """スコープ不一致時の再認証フローのテスト"""

    @pytest.fixture
    def mock_credentials_path(self, tmp_path: Path) -> Path:
        """モック認証情報パスのフィクスチャ."""
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{"installed": {"client_id": "test"}}')
        return creds_path

    @pytest.fixture
    def mock_token_path(self, tmp_path: Path) -> Path:
        """モックトークンパスのフィクスチャ."""
        token_path = tmp_path / "token.json"
        token_path.write_text(json.dumps({"token": "mock", "refresh_token": "mock_refresh"}))
        return token_path

    def test_scope_mismatch_triggers_reauth(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """スコープ不一致時に再認証フローが起動される."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            # 既存トークンは Calendar スコープのみ（Drive スコープ欠落）
            mock_old_creds = MagicMock()
            mock_old_creds.valid = True
            mock_old_creds.scopes = {"https://www.googleapis.com/auth/calendar"}
            mock_creds_cls.from_authorized_user_file.return_value = mock_old_creds

            # 新規認証フロー
            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "new_with_all_scopes"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            # 新規フローが起動されていること
            mock_flow_cls.from_client_secrets_file.assert_called_once_with(
                str(mock_credentials_path), SCOPES
            )
            assert result is mock_new_creds

    def test_scope_match_skips_reauth(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """スコープ一致時は再認証フローをスキップする."""
        with patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls:
            mock_creds = MagicMock()
            mock_creds.valid = True
            # SCOPES と一致するスコープセット
            mock_creds.scopes = set(SCOPES)
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            assert result is mock_creds

    def test_scope_mismatch_logs_warning(
        self, mock_credentials_path: Path, mock_token_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """スコープ不一致時に WARNING ログが出力される."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            mock_old_creds = MagicMock()
            mock_old_creds.valid = True
            mock_old_creds.scopes = {"https://www.googleapis.com/auth/calendar"}
            mock_creds_cls.from_authorized_user_file.return_value = mock_old_creds

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "new"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            with caplog.at_level(logging.WARNING):
                authenticate(str(mock_credentials_path), str(mock_token_path))

            assert any("スコープが変更されました" in record.message for record in caplog.records)

    def test_scope_none_triggers_reauth(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """トークンの scopes が None の場合に再認証フローが起動される."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            mock_old_creds = MagicMock()
            mock_old_creds.valid = True
            mock_old_creds.scopes = None
            mock_creds_cls.from_authorized_user_file.return_value = mock_old_creds

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "new"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            mock_flow_cls.from_client_secrets_file.assert_called_once()
            assert result is mock_new_creds


class TestRefreshErrorFallback:
    """RefreshError 発生時のフォールバックテスト"""

    @pytest.fixture
    def mock_credentials_path(self, tmp_path: Path) -> Path:
        """モック認証情報パスのフィクスチャ."""
        creds_path = tmp_path / "credentials.json"
        creds_path.write_text('{"installed": {"client_id": "test"}}')
        return creds_path

    @pytest.fixture
    def mock_token_path(self, tmp_path: Path) -> Path:
        """モックトークンパスのフィクスチャ."""
        token_path = tmp_path / "token.json"
        token_path.write_text(json.dumps({"token": "mock", "refresh_token": "mock_refresh"}))
        return token_path

    def test_refresh_error_triggers_reauth(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """RefreshError 発生時にフォールバック再認証が起動される."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.Request") as mock_request,
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "mock_refresh"
            mock_creds.scopes = set(SCOPES)  # スコープは一致
            mock_creds.refresh.side_effect = RefreshError("invalid_scope: Bad Request")
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "reauthed"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            result = authenticate(str(mock_credentials_path), str(mock_token_path))

            # refresh が呼ばれたこと
            mock_creds.refresh.assert_called_once_with(mock_request())
            # フォールバックで新規認証が起動されたこと
            mock_flow_cls.from_client_secrets_file.assert_called_once_with(
                str(mock_credentials_path), SCOPES
            )
            assert result is mock_new_creds

    def test_refresh_error_logs_warning(
        self, mock_credentials_path: Path, mock_token_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RefreshError 発生時に WARNING ログが出力される."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.Request"),
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "mock_refresh"
            mock_creds.scopes = set(SCOPES)
            mock_creds.refresh.side_effect = RefreshError("invalid_scope: Bad Request")
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "reauthed"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            with caplog.at_level(logging.WARNING):
                authenticate(str(mock_credentials_path), str(mock_token_path))

            assert any(
                "トークンリフレッシュに失敗" in record.message for record in caplog.records
            )

    def test_refresh_error_saves_new_token(
        self, mock_credentials_path: Path, mock_token_path: Path
    ) -> None:
        """RefreshError フォールバック後に新しいトークンが保存される."""
        with (
            patch(f"{_AUTH_MODULE}.Credentials") as mock_creds_cls,
            patch(f"{_AUTH_MODULE}.Request"),
            patch(f"{_AUTH_MODULE}.InstalledAppFlow") as mock_flow_cls,
        ):
            mock_creds = MagicMock()
            mock_creds.valid = False
            mock_creds.expired = True
            mock_creds.refresh_token = "mock_refresh"
            mock_creds.scopes = set(SCOPES)
            mock_creds.refresh.side_effect = RefreshError("invalid_scope: Bad Request")
            mock_creds_cls.from_authorized_user_file.return_value = mock_creds

            mock_flow = MagicMock()
            mock_new_creds = MagicMock()
            mock_new_creds.to_json.return_value = '{"token": "reauthed_saved"}'
            mock_flow.run_local_server.return_value = mock_new_creds
            mock_flow_cls.from_client_secrets_file.return_value = mock_flow

            authenticate(str(mock_credentials_path), str(mock_token_path))

            assert mock_token_path.read_text() == '{"token": "reauthed_saved"}'
