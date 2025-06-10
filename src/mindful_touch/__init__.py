"""Mindful Touch - Hand movement awareness tool."""

__version__ = "0.1.1"

from .config import AppConfig, get_config, get_config_manager
from .detector import DetectionResult, HandFaceDetector
from .main import MindfulTouchApp, main
from .notifier import NotificationManager

__all__ = [
    "HandFaceDetector",
    "NotificationManager",
    "MindfulTouchApp",
    "get_config",
    "get_config_manager",
    "main",
    "DetectionResult",
    "AppConfig",
]
