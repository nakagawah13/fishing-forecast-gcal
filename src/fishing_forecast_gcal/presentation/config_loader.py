"""Configuration file loader."""

import pathlib
from dataclasses import dataclass
from typing import Any

import yaml

from fishing_forecast_gcal.domain.models.location import Location


@dataclass(frozen=True)
class AppSettings:
    """Application settings.

    Attributes:
        timezone: Timezone string (e.g., "Asia/Tokyo")
        update_interval_hours: Update interval in hours
        forecast_window_days: Forecast window in days
        tide_register_months: How many months ahead to register tide events
        high_priority_hours: List of high priority hours (0-23)
        google_credentials_path: Path to OAuth credentials JSON
        google_token_path: Path to OAuth token JSON
        calendar_id: Google Calendar ID
    """

    timezone: str
    update_interval_hours: int
    forecast_window_days: int
    tide_register_months: int
    high_priority_hours: list[int]
    google_credentials_path: str
    google_token_path: str
    calendar_id: str


@dataclass(frozen=True)
class FishingConditionSettings:
    """Fishing condition settings.

    Attributes:
        prime_time_offset_hours: Prime time offset hours around high tide
        max_wind_speed_ms: Maximum wind speed threshold (m/s)
        preferred_tide_types: Preferred tide types
    """

    prime_time_offset_hours: int
    max_wind_speed_ms: float
    preferred_tide_types: list[str]


@dataclass(frozen=True)
class AppConfig:
    """Application configuration.

    Attributes:
        settings: Application settings
        locations: List of fishing locations
        fishing_conditions: Fishing condition settings
    """

    settings: AppSettings
    locations: list[Location]
    fishing_conditions: FishingConditionSettings


def load_config(config_path: str = "config/config.yaml") -> AppConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        AppConfig instance with validated configuration

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If configuration schema is invalid
    """
    config_file = pathlib.Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please create config/config.yaml from config/config.yaml.template"
        )

    with open(config_file, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")

    # Validate required top-level keys
    required_keys = ["settings", "locations"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key in config: {key}")

    # Parse and validate settings
    settings = _parse_settings(config["settings"])

    # Parse and validate locations
    locations = _parse_locations(config["locations"])

    # Parse and validate fishing_conditions (optional)
    fishing_conditions = _parse_fishing_conditions(config.get("fishing_conditions", {}))

    return AppConfig(
        settings=settings,
        locations=locations,
        fishing_conditions=fishing_conditions,
    )


def _parse_settings(settings_dict: dict[str, Any]) -> AppSettings:
    """Parse and validate settings section.

    Args:
        settings_dict: Settings dictionary from config

    Returns:
        AppSettings instance

    Raises:
        ValueError: If settings are invalid
    """
    required_keys = [
        "timezone",
        "update_interval_hours",
        "forecast_window_days",
        "tide_register_months",
        "high_priority_hours",
        "google_credentials_path",
        "google_token_path",
        "calendar_id",
    ]

    for key in required_keys:
        if key not in settings_dict:
            raise ValueError(f"Missing required key in settings: {key}")

    # Type validation
    try:
        timezone = str(settings_dict["timezone"])
        update_interval_hours = int(settings_dict["update_interval_hours"])
        forecast_window_days = int(settings_dict["forecast_window_days"])
        tide_register_months = int(settings_dict["tide_register_months"])
        high_priority_hours = [int(h) for h in settings_dict["high_priority_hours"]]
        google_credentials_path = str(settings_dict["google_credentials_path"])
        google_token_path = str(settings_dict["google_token_path"])
        calendar_id = str(settings_dict["calendar_id"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid type in settings: {e}") from e

    # Range validation
    if update_interval_hours < 1:
        raise ValueError("update_interval_hours must be >= 1")

    if forecast_window_days < 1:
        raise ValueError("forecast_window_days must be >= 1")

    if tide_register_months < 1:
        raise ValueError("tide_register_months must be >= 1")

    for hour in high_priority_hours:
        if not (0 <= hour <= 23):
            raise ValueError(f"high_priority_hours must be 0-23, got {hour}")

    # Validate credentials path exists
    if not pathlib.Path(google_credentials_path).exists():
        raise ValueError(f"Google credentials file not found: {google_credentials_path}")

    return AppSettings(
        timezone=timezone,
        update_interval_hours=update_interval_hours,
        forecast_window_days=forecast_window_days,
        tide_register_months=tide_register_months,
        high_priority_hours=high_priority_hours,
        google_credentials_path=google_credentials_path,
        google_token_path=google_token_path,
        calendar_id=calendar_id,
    )


def _parse_locations(locations_list: list[dict[str, Any]]) -> list[Location]:
    """Parse and validate locations section.

    Args:
        locations_list: List of location dictionaries

    Returns:
        List of Location instances

    Raises:
        ValueError: If locations are invalid
    """
    if not locations_list:
        raise ValueError("locations must not be empty")

    locations = []
    for i, loc_dict in enumerate(locations_list):
        try:
            location = Location(
                id=str(loc_dict["id"]),
                name=str(loc_dict["name"]),
                latitude=float(loc_dict["latitude"]),
                longitude=float(loc_dict["longitude"]),
                station_id=str(loc_dict["station_id"]),
            )
            locations.append(location)
        except KeyError as e:
            raise ValueError(f"Missing key in locations[{i}]: {e}") from e
        except (TypeError, ValueError) as e:
            raise ValueError(f"Invalid value in locations[{i}]: {e}") from e

    return locations


def _parse_fishing_conditions(fishing_conditions_dict: dict[str, Any]) -> FishingConditionSettings:
    """Parse and validate fishing_conditions section.

    Args:
        fishing_conditions_dict: Fishing conditions dictionary (optional)

    Returns:
        FishingConditionSettings instance with defaults if not provided

    Raises:
        ValueError: If fishing_conditions are invalid
    """
    # Provide defaults for optional section
    defaults: dict[str, Any] = {
        "prime_time_offset_hours": 2,
        "max_wind_speed_ms": 10.0,
        "preferred_tide_types": ["大潮", "中潮"],
    }

    merged: dict[str, Any] = {**defaults, **fishing_conditions_dict}

    try:
        prime_time_offset_hours_raw = merged["prime_time_offset_hours"]
        max_wind_speed_ms_raw = merged["max_wind_speed_ms"]
        preferred_tide_types_raw = merged["preferred_tide_types"]

        # Type validation and conversion
        prime_time_offset_hours = int(prime_time_offset_hours_raw)
        max_wind_speed_ms = float(max_wind_speed_ms_raw)

        if not isinstance(preferred_tide_types_raw, list):
            raise ValueError("preferred_tide_types must be a list")
        preferred_tide_types = [str(t) for t in preferred_tide_types_raw]
    except (TypeError, ValueError, KeyError) as e:
        raise ValueError(f"Invalid type in fishing_conditions: {e}") from e

    # Range validation
    if prime_time_offset_hours < 1:
        raise ValueError("prime_time_offset_hours must be >= 1")

    if max_wind_speed_ms < 0:
        raise ValueError("max_wind_speed_ms must be >= 0")

    return FishingConditionSettings(
        prime_time_offset_hours=prime_time_offset_hours,
        max_wind_speed_ms=max_wind_speed_ms,
        preferred_tide_types=preferred_tide_types,
    )
