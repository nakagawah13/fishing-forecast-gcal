"""CLI entry point for fishing-forecast-gcal."""

import sys
from pathlib import Path

from fishing_forecast_gcal.infrastructure.clients.google_calendar_client import (
    GoogleCalendarClient,
)
from fishing_forecast_gcal.presentation.config_loader import load_config


def main() -> None:
    """Main CLI entry point."""
    print("=" * 70)
    print("fishing-forecast-gcal - Fishing forecast calendar integration")
    print("Version: 0.1.0")
    print("=" * 70)
    print()

    try:
        # Load configuration
        print("[1/3] Loading configuration...")
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            print("❌ Error: config/config.yaml not found")
            print("Please create config/config.yaml from config/config.yaml.template")
            sys.exit(1)

        config = load_config(str(config_path))
        settings = config["settings"]
        print(f"✅ Configuration loaded from: {config_path}")
        print(f"   - Timezone: {settings['timezone']}")
        print(f"   - Calendar ID: {settings['calendar_id'][:30]}...")
        print()

        # Initialize Google Calendar client
        print("[2/3] Authenticating with Google Calendar API...")
        credentials_path = settings["google_credentials_path"]
        token_path = settings["google_token_path"]

        client = GoogleCalendarClient(credentials_path, token_path)
        client.authenticate()
        print("✅ Authentication successful")
        print()

        # Test connection
        print("[3/3] Testing Calendar API connection...")
        if client.test_connection():
            print("✅ Connection test successful")
        else:
            print("❌ Connection test failed")
            sys.exit(1)

        print()
        print("=" * 70)
        print("🎉 Setup completed successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Implement domain models (T-001)")
        print("2. Implement repository interfaces (T-002)")
        print("3. Implement tide calculation service (T-003)")
        print()
        print("For more information, see docs/implementation_plan.md")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
