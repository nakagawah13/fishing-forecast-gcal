"""Google Calendar API client with OAuth2 authentication."""

import pathlib
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth2 scopes required for Google Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarClient:
    """Client for Google Calendar API with OAuth2 authentication."""

    def __init__(self, credentials_path: str, token_path: str) -> None:
        """Initialize Google Calendar client.

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to store OAuth2 token JSON file
        """
        self.credentials_path = pathlib.Path(credentials_path)
        self.token_path = pathlib.Path(token_path)
        self._creds: Credentials | None = None
        self._service: Any = None

    def authenticate(self) -> None:
        """Perform OAuth2 authentication flow.

        This will:
        1. Load existing token if available
        2. Refresh token if expired
        3. Prompt user for authorization if no valid token exists
        4. Save token for future use
        """
        # Load existing token
        if self.token_path.exists():
            self._creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # If no valid credentials, perform OAuth flow
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                # Refresh expired token
                print("Refreshing OAuth token...")
                self._creds.refresh(Request())
            else:
                # Perform new OAuth flow
                print("Starting OAuth authentication flow...")
                print(f"Using credentials from: {self.credentials_path}")
                
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please download OAuth2 credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                self._creds = flow.run_local_server(port=0)
                print("Authentication successful!")

            # Save token for future use
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, "w") as token_file:
                token_file.write(self._creds.to_json())
            print(f"Token saved to: {self.token_path}")

        # Build Calendar API service
        self._service = build("calendar", "v3", credentials=self._creds)

    def get_service(self) -> Any:
        """Get authenticated Calendar API service.

        Returns:
            Authenticated Google Calendar API service instance

        Raises:
            RuntimeError: If authentication has not been performed
        """
        if self._service is None:
            raise RuntimeError(
                "Calendar service not initialized. Call authenticate() first."
            )
        return self._service

    def test_connection(self) -> bool:
        """Test Calendar API connection by fetching calendar list.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            service = self.get_service()
            result = service.calendarList().list(maxResults=10).execute()
            calendars = result.get("items", [])
            
            print("\n=== Available Calendars ===")
            for calendar in calendars:
                print(f"- {calendar['summary']}: {calendar['id']}")
            print(f"\nTotal: {len(calendars)} calendar(s) found")
            
            return True
        except Exception as e:
            print(f"Error testing connection: {e}")
            return False
