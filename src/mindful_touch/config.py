"""
Configuration management for Mindful Touch.

This module handles loading, validation, and management of application settings
using Pydantic models for type safety and validation.
"""

import json
import platform
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, validator
from platformdirs import user_config_dir, user_data_dir


class DetectionConfig(BaseModel):
    """Configuration for hand-to-face detection parameters."""
    
    sensitivity: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="Detection sensitivity (0.1-1.0, higher = more sensitive)"
    )
    hand_face_threshold_cm: float = Field(
        default=15.0,
        ge=2.0,
        le=50.0,
        description="Distance threshold in cm for hand-to-face detection"
    )
    detection_interval_ms: int = Field(
        default=100,
        ge=50,
        le=1000,
        description="Interval between detections in milliseconds"
    )
    confidence_threshold: float = Field(
        default=0.6,
        ge=0.3,
        le=0.95,
        description="Minimum confidence for hand/face detection"
    )


class NotificationConfig(BaseModel):
    """Configuration for desktop notifications."""
    
    enabled: bool = Field(
        default=True,
        description="Whether notifications are enabled"
    )
    title: str = Field(
        default="Mindful Moment",
        description="Notification title"
    )
    message: str = Field(
        default="Take a gentle pause 🌸",
        description="Notification message"
    )
    duration_seconds: int = Field(
        default=3,
        ge=1,
        le=30,
        description="How long notification stays visible"
    )
    cooldown_seconds: int = Field(
        default=10,
        ge=5,
        le=300,
        description="Minimum time between notifications"
    )


class CameraConfig(BaseModel):
    """Configuration for camera settings."""
    
    device_id: int = Field(
        default=0,
        ge=0,
        description="Camera device ID (usually 0 for default camera)"
    )
    width: int = Field(
        default=640,
        ge=320,
        le=1920,
        description="Camera capture width in pixels"
    )
    height: int = Field(
        default=480,
        ge=240,
        le=1080,
        description="Camera capture height in pixels"
    )
    fps: int = Field(
        default=30,
        ge=10,
        le=60,
        description="Frames per second for camera capture"
    )
    
    @validator('width', 'height')
    def validate_dimensions(cls, v: int) -> int:
        """Ensure dimensions are multiples of 32 for better performance."""
        return (v // 32) * 32


class PrivacyConfig(BaseModel):
    """Configuration for privacy and data handling."""
    
    save_images: bool = Field(
        default=False,
        description="Whether to save captured images (for debugging only)"
    )
    log_detections: bool = Field(
        default=False,
        description="Whether to log detection events"
    )


class AppConfig(BaseModel):
    """Main application configuration."""
    
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"  # Don't allow unknown fields


class ConfigManager:
    """Manages application configuration loading, saving, and validation."""
    
    def __init__(self, app_name: str = "mindful-touch") -> None:
        """Initialize configuration manager.
        
        Args:
            app_name: Name of the application for config directory
        """
        self.app_name = app_name
        self._config_dir = Path(user_config_dir(app_name))
        self._data_dir = Path(user_data_dir(app_name))
        self._config_file = self._config_dir / "settings.json"
        self._default_config_file = Path(__file__).parent.parent.parent / "config" / "default_settings.json"
        
        # Ensure directories exist
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        self._config: Optional[AppConfig] = None
    
    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self._config_dir
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory path."""
        return self._data_dir
    
    def load_config(self) -> AppConfig:
        """Load configuration from file or create default.
        
        Returns:
            Loaded and validated application configuration
            
        Raises:
            ValueError: If configuration file is invalid
            FileNotFoundError: If default config is missing and no user config exists
        """
        if self._config is not None:
            return self._config
        
        config_data = {}
        
        # Try to load user configuration
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                print(f"✅ Loaded configuration from {self._config_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Error reading user config: {e}")
                print("📝 Will use default configuration")
        
        # Load default configuration as fallback
        elif self._default_config_file.exists():
            try:
                with open(self._default_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                print(f"📋 Using default configuration from {self._default_config_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"❌ Error reading default config: {e}")
        
        # Create and validate configuration
        try:
            self._config = AppConfig(**config_data)
            return self._config
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")
    
    def save_config(self, config: Optional[AppConfig] = None) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration to save. If None, saves current config.
            
        Raises:
            ValueError: If no configuration is available to save
        """
        if config is None:
            config = self._config
        
        if config is None:
            raise ValueError("No configuration available to save")
        
        try:
            config_dict = config.dict()
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"💾 Configuration saved to {self._config_file}")
            self._config = config
        except IOError as e:
            raise ValueError(f"Failed to save configuration: {e}")
    
    def reset_to_defaults(self) -> AppConfig:
        """Reset configuration to defaults and save.
        
        Returns:
            Default configuration
        """
        self._config = AppConfig()
        self.save_config()
        print("🔄 Configuration reset to defaults")
        return self._config
    
    def update_config(self, **kwargs) -> AppConfig:
        """Update specific configuration values.
        
        Args:
            **kwargs: Configuration values to update (nested dict format)
            
        Returns:
            Updated configuration
            
        Example:
            manager.update_config(
                detection={'sensitivity': 0.8},
                notifications={'enabled': False}
            )
        """
        config = self.load_config()
        config_dict = config.dict()
        
        # Deep update of configuration
        for key, value in kwargs.items():
            if key in config_dict and isinstance(value, dict):
                config_dict[key].update(value)
            else:
                config_dict[key] = value
        
        # Recreate and validate config
        updated_config = AppConfig(**config_dict)
        self.save_config(updated_config)
        return updated_config
    
    def get_platform_specific_config(self) -> dict:
        """Get platform-specific configuration adjustments.
        
        Returns:
            Dictionary of platform-specific settings
        """
        system = platform.system().lower()
        
        adjustments = {}
        
        if system == "darwin":  # macOS
            # macOS cameras sometimes need different settings
            adjustments.update({
                "camera": {"fps": 24}  # Some macOS cameras prefer 24fps
            })
        elif system == "linux":
            # Linux might need different notification settings
            adjustments.update({
                "notifications": {"duration_seconds": 5}  # Linux notifications might need longer duration
            })
        elif system == "windows":
            # Windows-specific adjustments
            pass
        
        return adjustments


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance.
    
    Returns:
        Global ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get the current application configuration.
    
    Returns:
        Current application configuration
    """
    return get_config_manager().load_config()