"""Google Calendar API client with OAuth2 authentication."""

import pathlib
from datetime import UTC
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth2 scopes required for Google Calendar + Drive API
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]


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

                flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
                self._creds = flow.run_local_server(port=0)  # type: ignore[assignment]
                print("Authentication successful!")

            # Save token for future use
            assert self._creds is not None
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
            raise RuntimeError("Calendar service not initialized. Call authenticate() first.")
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

    def create_event(
        self,
        calendar_id: str,
        event_id: str,
        summary: str,
        description: str,
        start_date: Any,
        end_date: Any,
        timezone: str = "Asia/Tokyo",
        extended_properties: dict[str, str] | None = None,
        attachments: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Create a new calendar event.

        Args:
            calendar_id: Calendar ID to create event in
            event_id: Unique event ID (for idempotency)
            summary: Event title
            description: Event description (body text)
            start_date: Event start date (date object)
            end_date: Event end date (date object, exclusive)
            timezone: Timezone for the event (default: Asia/Tokyo)
            extended_properties: Custom metadata (key-value pairs)
            attachments: List of file attachment dicts with fileUrl, title,
                mimeType keys (optional). Requires supportsAttachments=True.

        Returns:
            Created event details from Google Calendar API

        Raises:
            RuntimeError: If calendar service is not initialized
            HttpError: If API call fails
        """
        from datetime import date

        service = self.get_service()

        # Convert date objects to ISO string format
        if isinstance(start_date, date):
            start_date_str = start_date.isoformat()
        else:
            start_date_str = str(start_date)

        if isinstance(end_date, date):
            end_date_str = end_date.isoformat()
        else:
            end_date_str = str(end_date)

        event_body: dict[str, Any] = {
            "id": event_id,
            "summary": summary,
            "description": description,
            "start": {"date": start_date_str, "timeZone": timezone},
            "end": {"date": end_date_str, "timeZone": timezone},
        }

        # Add extended properties if provided
        if extended_properties:
            event_body["extendedProperties"] = {"private": extended_properties}

        # Add attachments if provided
        if attachments:
            event_body["attachments"] = attachments

        result = (
            service.events()
            .insert(
                calendarId=calendar_id,
                body=event_body,
                supportsAttachments=True,
            )
            .execute()
        )
        return result  # type: ignore[no-any-return]

    def get_event(self, calendar_id: str, event_id: str) -> dict[str, Any] | None:
        """Get a calendar event by ID.

        Args:
            calendar_id: Calendar ID to search in
            event_id: Event ID to retrieve

        Returns:
            Event details if found, None if not found

        Raises:
            RuntimeError: If calendar service is not initialized
        """
        from googleapiclient.errors import HttpError

        service = self.get_service()

        try:
            result = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            return result  # type: ignore[no-any-return]
        except HttpError as e:
            if e.resp.status == 404:
                # Event not found
                return None
            # Re-raise other errors
            raise

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        summary: str | None = None,
        description: str | None = None,
        start_date: Any = None,
        end_date: Any = None,
        timezone: str = "Asia/Tokyo",
        extended_properties: dict[str, str] | None = None,
        attachments: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Update an existing calendar event.

        Args:
            calendar_id: Calendar ID containing the event
            event_id: Event ID to update
            summary: New event title (optional)
            description: New event description (optional)
            start_date: New start date (optional)
            end_date: New end date (optional)
            timezone: Timezone for the event (default: Asia/Tokyo)
            extended_properties: Custom metadata (key-value pairs, optional)
            attachments: List of file attachment dicts with fileUrl, title,
                mimeType keys (optional). Requires supportsAttachments=True.

        Returns:
            Updated event details from Google Calendar API

        Raises:
            RuntimeError: If event not found or calendar service not initialized
            HttpError: If API call fails
        """
        from datetime import date

        from googleapiclient.errors import HttpError

        service = self.get_service()

        # First, get the existing event
        try:
            service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise RuntimeError(f"Event not found: {event_id}") from e
            raise

        # Build update body with only provided fields
        update_body: dict[str, Any] = {}

        if summary is not None:
            update_body["summary"] = summary

        if description is not None:
            update_body["description"] = description

        if start_date is not None:
            if isinstance(start_date, date):
                start_date_str = start_date.isoformat()
            else:
                start_date_str = str(start_date)
            update_body["start"] = {"date": start_date_str, "timeZone": timezone}

        if end_date is not None:
            if isinstance(end_date, date):
                end_date_str = end_date.isoformat()
            else:
                end_date_str = str(end_date)
            update_body["end"] = {"date": end_date_str, "timeZone": timezone}

        # Add extended properties if provided
        if extended_properties is not None:
            update_body["extendedProperties"] = {"private": extended_properties}

        # Add attachments if provided
        if attachments is not None:
            update_body["attachments"] = attachments

        # Use patch for partial update
        result = (
            service.events()
            .patch(
                calendarId=calendar_id,
                eventId=event_id,
                body=update_body,
                supportsAttachments=True,
            )
            .execute()
        )
        return result  # type: ignore[no-any-return]

    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete a calendar event by ID (idempotent).

        If the event does not exist (404), returns False without raising.
        (削除対象が存在しない場合は False を返し、エラーにしない)

        Args:
            calendar_id: Calendar ID containing the event
            event_id: Event ID to delete

        Returns:
            True if the event was deleted, False if it did not exist

        Raises:
            RuntimeError: If calendar service is not initialized
            HttpError: If API call fails (except 404)
        """
        from googleapiclient.errors import HttpError

        service = self.get_service()

        try:
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                return False
            raise

    def list_events(
        self,
        calendar_id: str,
        start_date: Any,
        end_date: Any,
        private_extended_property: str | None = None,
        max_results: int = 2500,
    ) -> list[dict[str, Any]]:
        """List calendar events within a date range.

        Retrieves all events in the specified period, optionally filtered
        by private extended property.
        (指定期間のイベントを取得。extendedProperty でフィルタ可能)

        Args:
            calendar_id: Calendar ID to search in
            start_date: Start date (inclusive, date object)
            end_date: End date (inclusive, date object)
            private_extended_property: Filter by private extended property
                (format: "key=value", e.g. "location_id=tk")
            max_results: Maximum number of results per page (default: 2500)

        Returns:
            List of event dictionaries from Google Calendar API

        Raises:
            RuntimeError: If calendar service is not initialized
            HttpError: If API call fails
        """
        from datetime import date, datetime

        service = self.get_service()

        # Convert date to RFC3339 datetime strings
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            time_min = datetime(
                start_date.year, start_date.month, start_date.day, tzinfo=UTC
            ).isoformat()
        else:
            time_min = str(start_date)

        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            # end_date is inclusive, so add 1 day
            from datetime import timedelta

            next_day = end_date + timedelta(days=1)
            time_max = datetime(next_day.year, next_day.month, next_day.day, tzinfo=UTC).isoformat()
        else:
            time_max = str(end_date)

        all_events: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            kwargs: dict[str, Any] = {
                "calendarId": calendar_id,
                "timeMin": time_min,
                "timeMax": time_max,
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime",
            }

            if private_extended_property:
                kwargs["privateExtendedProperty"] = private_extended_property

            if page_token:
                kwargs["pageToken"] = page_token

            result = service.events().list(**kwargs).execute()
            events = result.get("items", [])
            all_events.extend(events)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_events
