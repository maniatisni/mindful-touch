"""
Mindful Touch - A gentle awareness tool for mindful hand movement tracking.

This package provides real-time hand-to-face proximity detection using computer vision
to help users develop awareness of unconscious hand movements through gentle notifications.

Key Features:
- Real-time hand and face detection using MediaPipe
- Configurable sensitivity and distance thresholds  
- Cross-platform desktop notifications
- Privacy-first: all processing happens locally
- CLI interface for easy use
- Calibration system for personalized setup

Example Usage:
    from mindful_touch import get_config, create_detector, create_notification_manager
    
    config = get_config()
    detector = create_detector(config.detection, config.camera)
    notifier = create_notification_manager(config.notifications)
    
    detector.start_detection()
    while True:
        result = detector.capture_and_detect()
        if result and result.event:
            notifier.show_mindful_moment()

CLI Usage:
    mindful-touch start                    # Start monitoring
    mindful-touch calibrate               # Calibrate for your setup  
    mindful-touch config --sensitivity 0.8 # Adjust settings
    mindful-touch test                    # Test notifications
"""

__version__ = "0.1.0"
__author__ = "Mindful Touch Team"
__description__ = "A gentle awareness tool for mindful hand movement tracking"

# Core imports for easy access
from .config import (
    get_config,
    get_config_manager,
    AppConfig,
    DetectionConfig,
    NotificationConfig,
    CameraConfig,
    PrivacyConfig
)

from .detector import (
    create_detector,
    HandFaceDetector,
    DetectionResult,
    DetectionEvent,
    Point3D
)

from .notifier import (
    create_notification_manager,
    NotificationManager
)

from .main import MindfulTouchApp

__all__ = [
    # Core classes
    "MindfulTouchApp",
    "HandFaceDetector", 
    "NotificationManager",
    
    # Configuration
    "AppConfig",
    "DetectionConfig", 
    "NotificationConfig",
    "CameraConfig",
    "PrivacyConfig",
    "get_config",
    "get_config_manager",
    
    # Factory functions
    "create_detector",
    "create_notification_manager",
    
    # Data types
    "DetectionResult",
    "DetectionEvent", 
    "Point3D",
    
    # Metadata
    "__version__",
    "__author__",
    "__description__"
]