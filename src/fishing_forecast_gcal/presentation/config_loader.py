"""Configuration file loader."""

import pathlib
from typing import Any

import yaml


def load_config(config_path: str = "config/config.yaml") -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    config_file = pathlib.Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please create config/config.yaml from config/config.yaml.template"
        )
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")
    
    # Validate required keys
    required_keys = ["settings", "locations"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required key in config: {key}")
    
    return config
