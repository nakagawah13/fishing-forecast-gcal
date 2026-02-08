"""Unit tests for config_loader."""

from pathlib import Path
from typing import Any

import pytest
import yaml

from fishing_forecast_gcal.domain.models.location import Location
from fishing_forecast_gcal.presentation.config_loader import (
    AppConfig,
    AppSettings,
    FishingConditionSettings,
    load_config,
)


@pytest.fixture
def valid_config_dict() -> dict[str, Any]:
    """Valid configuration dictionary."""
    return {
        "settings": {
            "timezone": "Asia/Tokyo",
            "update_interval_hours": 3,
            "forecast_window_days": 7,
            "tide_register_months": 12,
            "high_priority_hours": [4, 5, 6, 7, 20, 21, 22, 23],
            "google_credentials_path": "config/credentials.json",
            "google_token_path": "config/token.json",
            "calendar_id": "test@group.calendar.google.com",
        },
        "locations": [
            {
                "id": "loc_home",
                "name": "Home",
                "latitude": 35.0,
                "longitude": 139.0,
            }
        ],
        "fishing_conditions": {
            "prime_time_offset_hours": 2,
            "max_wind_speed_ms": 10.0,
            "preferred_tide_types": ["大潮", "中潮"],
        },
    }


@pytest.fixture
def temp_config_file(valid_config_dict: dict[str, Any], tmp_path: Path) -> Path:
    """Create a temporary valid config file."""
    config_path = tmp_path / "config.yaml"

    # Create credentials file
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text("{}")

    # Update credentials path to point to temp location
    valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

    config_path.write_text(yaml.dump(valid_config_dict))
    return config_path


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, temp_config_file: Path) -> None:
        """Test loading a valid configuration file."""
        config = load_config(str(temp_config_file))

        assert isinstance(config, AppConfig)
        assert isinstance(config.settings, AppSettings)
        assert isinstance(config.fishing_conditions, FishingConditionSettings)
        assert len(config.locations) == 1
        assert isinstance(config.locations[0], Location)

    def test_settings_values(self, temp_config_file: Path) -> None:
        """Test that settings are correctly parsed."""
        config = load_config(str(temp_config_file))
        settings = config.settings

        assert settings.timezone == "Asia/Tokyo"
        assert settings.update_interval_hours == 3
        assert settings.forecast_window_days == 7
        assert settings.tide_register_months == 12
        assert settings.high_priority_hours == [4, 5, 6, 7, 20, 21, 22, 23]
        assert settings.calendar_id == "test@group.calendar.google.com"

    def test_location_mapping(self, temp_config_file: Path) -> None:
        """Test that locations are mapped to Location model."""
        config = load_config(str(temp_config_file))
        location = config.locations[0]

        assert location.id == "loc_home"
        assert location.name == "Home"
        assert location.latitude == 35.0
        assert location.longitude == 139.0

    def test_fishing_conditions_values(self, temp_config_file: Path) -> None:
        """Test that fishing conditions are correctly parsed."""
        config = load_config(str(temp_config_file))
        conditions = config.fishing_conditions

        assert conditions.prime_time_offset_hours == 2
        assert conditions.max_wind_speed_ms == 10.0
        assert conditions.preferred_tide_types == ["大潮", "中潮"]

    def test_file_not_found(self) -> None:
        """Test error when config file does not exist."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            load_config("nonexistent.yaml")

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test error when config file is empty."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")

        with pytest.raises(ValueError, match="Configuration file is empty"):
            load_config(str(config_path))

    def test_missing_top_level_key(self, tmp_path: Path) -> None:
        """Test error when required top-level key is missing."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump({"settings": {}}))

        with pytest.raises(ValueError, match="Missing required key in config: locations"):
            load_config(str(config_path))

    def test_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test error when YAML syntax is invalid."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("invalid: yaml: syntax:")

        with pytest.raises(yaml.YAMLError):
            load_config(str(config_path))


class TestSettingsValidation:
    """Tests for settings validation."""

    def test_missing_required_setting_key(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test error when required setting key is missing."""
        del valid_config_dict["settings"]["timezone"]

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="Missing required key in settings: timezone"):
            load_config(str(config_path))

    def test_invalid_update_interval_hours(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test error when update_interval_hours is invalid."""
        valid_config_dict["settings"]["update_interval_hours"] = 0

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="update_interval_hours must be >= 1"):
            load_config(str(config_path))

    def test_invalid_high_priority_hour(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test error when high_priority_hours contains invalid value."""
        valid_config_dict["settings"]["high_priority_hours"] = [4, 5, 25]

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="high_priority_hours must be 0-23"):
            load_config(str(config_path))

    def test_credentials_file_not_found(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test error when credentials file does not exist."""
        valid_config_dict["settings"]["google_credentials_path"] = "nonexistent.json"

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="Google credentials file not found"):
            load_config(str(config_path))


class TestLocationsValidation:
    """Tests for locations validation."""

    def test_empty_locations(self, valid_config_dict: dict[str, Any], tmp_path: Path) -> None:
        """Test error when locations list is empty."""
        valid_config_dict["locations"] = []

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="locations must not be empty"):
            load_config(str(config_path))

    def test_missing_location_key(self, valid_config_dict: dict[str, Any], tmp_path: Path) -> None:
        """Test error when location has missing key."""
        del valid_config_dict["locations"][0]["id"]

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="Missing key in locations"):
            load_config(str(config_path))

    def test_invalid_latitude(self, valid_config_dict: dict[str, Any], tmp_path: Path) -> None:
        """Test error when latitude is out of range."""
        valid_config_dict["locations"][0]["latitude"] = 100.0

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="latitude must be between -90 and 90"):
            load_config(str(config_path))

    def test_invalid_longitude(self, valid_config_dict: dict[str, Any], tmp_path: Path) -> None:
        """Test error when longitude is out of range."""
        valid_config_dict["locations"][0]["longitude"] = 200.0

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="longitude must be between -180 and 180"):
            load_config(str(config_path))

    def test_multiple_locations(self, valid_config_dict: dict[str, Any], tmp_path: Path) -> None:
        """Test loading multiple locations."""
        valid_config_dict["locations"].append(
            {
                "id": "loc_away",
                "name": "Away",
                "latitude": 34.5,
                "longitude": 138.5,
            }
        )

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        config = load_config(str(config_path))
        assert len(config.locations) == 2
        assert config.locations[0].id == "loc_home"
        assert config.locations[1].id == "loc_away"


class TestFishingConditionsValidation:
    """Tests for fishing_conditions validation."""

    def test_optional_fishing_conditions(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test that fishing_conditions is optional with defaults."""
        del valid_config_dict["fishing_conditions"]

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        config = load_config(str(config_path))
        conditions = config.fishing_conditions

        # Check defaults
        assert conditions.prime_time_offset_hours == 2
        assert conditions.max_wind_speed_ms == 10.0
        assert conditions.preferred_tide_types == ["大潮", "中潮"]

    def test_partial_fishing_conditions(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test that partial fishing_conditions uses defaults for missing keys."""
        valid_config_dict["fishing_conditions"] = {
            "prime_time_offset_hours": 3,
        }

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        config = load_config(str(config_path))
        conditions = config.fishing_conditions

        # Check override and defaults
        assert conditions.prime_time_offset_hours == 3
        assert conditions.max_wind_speed_ms == 10.0
        assert conditions.preferred_tide_types == ["大潮", "中潮"]

    def test_invalid_prime_time_offset(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test error when prime_time_offset_hours is invalid."""
        valid_config_dict["fishing_conditions"]["prime_time_offset_hours"] = 0

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="prime_time_offset_hours must be >= 1"):
            load_config(str(config_path))

    def test_invalid_max_wind_speed(
        self, valid_config_dict: dict[str, Any], tmp_path: Path
    ) -> None:
        """Test error when max_wind_speed_ms is negative."""
        valid_config_dict["fishing_conditions"]["max_wind_speed_ms"] = -1.0

        credentials_path = tmp_path / "credentials.json"
        credentials_path.write_text("{}")
        valid_config_dict["settings"]["google_credentials_path"] = str(credentials_path)

        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(valid_config_dict))

        with pytest.raises(ValueError, match="max_wind_speed_ms must be >= 0"):
            load_config(str(config_path))
