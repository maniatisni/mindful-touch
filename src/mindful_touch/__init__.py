"""Mindful Touch - Hand movement awareness tool."""

__version__ = "0.1.0"

from .config import get_config, get_config_manager, AppConfig
from .detector import HandFaceDetector, DetectionResult, DetectionEvent
from .notifier import NotificationManager
from .main import main, MindfulTouchApp

__all__ = [
    "HandFaceDetector",
    "NotificationManager", 
    "MindfulTouchApp",
    "get_config",
    "get_config_manager",
    "main",
    "DetectionResult",
    "DetectionEvent",
    "AppConfig",
]