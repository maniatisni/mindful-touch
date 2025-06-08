"""Configuration management for Mindful Touch."""

import json
from pathlib import Path
from typing import Any, Optional

from platformdirs import user_config_dir
from pydantic import BaseModel, Field


class DetectionConfig(BaseModel):
    """Detection parameters."""

    sensitivity: float = Field(default=0.7, ge=0.1, le=1.0)
    hand_face_threshold_cm: float = Field(default=15.0, ge=2.0, le=50.0)
    detection_interval_ms: int = Field(default=100, ge=50, le=1000)
    confidence_threshold: float = Field(default=0.6, ge=0.3, le=0.95)


class NotificationConfig(BaseModel):
    """Notification settings."""

    enabled: bool = True
    title: str = "Mindful Moment"
    message: str = "Take a gentle pause 🌸"
    duration_seconds: int = Field(default=3, ge=1, le=30)
    cooldown_seconds: int = Field(default=10, ge=5, le=300)


class CameraConfig(BaseModel):
    """Camera settings."""

    device_id: int = Field(default=0, ge=0)
    width: int = Field(default=640, ge=320, le=1920)
    height: int = Field(default=480, ge=240, le=1080)
    fps: int = Field(default=30, ge=10, le=60)


class AppConfig(BaseModel):
    """Main configuration."""

    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)


class ConfigManager:
    """Manages application configuration."""

    def __init__(self) -> None:
        self._config_dir = Path(user_config_dir("mindful-touch"))
        self._config_file = self._config_dir / "settings.json"
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._config: Optional[AppConfig] = None

    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self._config:
            return self._config

        if self._config_file.exists():
            try:
                with open(self._config_file) as f:
                    self._config = AppConfig(**json.load(f))
            except Exception:
                self._config = AppConfig()
        else:
            self._config = AppConfig()

        return self._config

    def save_config(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file."""
        if not config:
            config = self._config
        if not config:
            return

        with open(self._config_file, "w") as f:
            json.dump(config.model_dump(), f, indent=2)
        self._config = config

    def update_config(self, **kwargs: Any) -> AppConfig:
        """Update specific configuration values."""
        config = self.load_config()
        config_dict = config.model_dump()

        for key, value in kwargs.items():
            if key in config_dict and isinstance(value, dict):
                config_dict[key].update(value)
            else:
                config_dict[key] = value

        updated_config = AppConfig(**config_dict)
        self.save_config(updated_config)
        return updated_config


_config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get current configuration."""
    return _config_manager.load_config()


def get_config_manager() -> ConfigManager:
    """Get configuration manager instance."""
    return _config_manager
