"""Google OAuth2 authentication helper module.

Provides a shared OAuth2 authentication flow used by
GoogleCalendarClient and GoogleDriveClient.

Centralizes SCOPES definition and token management to eliminate
duplication across Google API clients.

Main Components:
    - SCOPES: Combined OAuth2 scopes for Calendar and Drive APIs.
    - authenticate: Perform OAuth2 flow and return valid Credentials.

Project Context:
    Part of the infrastructure/clients layer. All Google API clients
    should delegate authentication to this module.

Example:
    >>> from fishing_forecast_gcal.infrastructure.clients.google_auth import (
    ...     authenticate,
    ... )
    >>> creds = authenticate("config/credentials.json", "config/token.json")
"""

import logging
import pathlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

# OAuth2 scopes required for Google Calendar + Drive API
# (Google Calendar + Drive API に必要な OAuth2 スコープ)
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]


def authenticate(credentials_path: str, token_path: str) -> Credentials:
    """Perform OAuth2 authentication and return valid Credentials.

    Executes the standard Google OAuth2 flow:
    1. Load existing token if available.
    2. Refresh token if expired.
    3. Prompt user for authorization if no valid token exists.
    4. Save token for future use.

    (Google OAuth2 認証を実行し、有効な Credentials を返す)

    Args:
        credentials_path: Path to OAuth2 credentials JSON file.
                          (OAuth2 認証情報 JSON ファイルのパス)
        token_path: Path to store/load OAuth2 token JSON file.
                    (OAuth2 トークン JSON ファイルの保存/読み込みパス)

    Returns:
        Credentials: Valid Google OAuth2 credentials.
                     (有効な Google OAuth2 認証情報)

    Raises:
        FileNotFoundError: If credentials file does not exist when
            new authorization is needed.
            (新規認証が必要な際に credentials ファイルが存在しない場合)
    """
    creds_path = pathlib.Path(credentials_path)
    tok_path = pathlib.Path(token_path)
    creds: Credentials | None = None

    # Load existing token
    if tok_path.exists():
        creds = Credentials.from_authorized_user_file(str(tok_path), SCOPES)

    # If no valid credentials, perform OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            logger.info("Refreshing OAuth token...")
            creds.refresh(Request())
        else:
            # Perform new OAuth flow
            logger.info("Starting OAuth authentication flow...")
            logger.info("Using credentials from: %s", creds_path)

            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Credentials file not found: {creds_path}\n"
                    "Please download OAuth2 credentials from Google Cloud Console."
                )

            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)  # type: ignore[assignment]
            logger.info("Authentication successful!")

        # Save token for future use
        assert creds is not None
        tok_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tok_path, "w") as token_file:
            token_file.write(creds.to_json())
        logger.info("Token saved to: %s", tok_path)

    return creds
