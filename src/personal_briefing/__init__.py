"""Personal briefing - daily AI-powered news digest."""

from pathlib import Path

import yaml

from personal_briefing.models import Config

__version__ = "0.1.0"

_config_cache: Config | None = None


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses bundled config.

    Returns:
        Parsed configuration object.
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    if config_path is None:
        # In Lambda, files are at /var/task
        # Try Lambda path first, fall back to development path
        lambda_path = Path("/var/task/config/topics.yaml")
        dev_path = Path(__file__).parent.parent.parent / "config" / "topics.yaml"
        config_path = lambda_path if lambda_path.exists() else dev_path
    else:
        config_path = Path(config_path)

    with open(config_path, encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    _config_cache = Config(**config_data)
    return _config_cache


def reset_config_cache() -> None:
    """Reset the config cache. Useful for testing."""
    global _config_cache
    _config_cache = None
