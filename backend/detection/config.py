# Configuration for Mindful Touch Multi-Region Detection
# Clean, focused configuration


class Config:
    # Camera settings
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720

    # MediaPipe settings
    HAND_DETECTION_CONFIDENCE = 0.7
    HAND_TRACKING_CONFIDENCE = 0.7
    FACE_DETECTION_CONFIDENCE = 0.7
    FACE_TRACKING_CONFIDENCE = 0.7

    # Detection settings
    CONTACT_THRESHOLD = 0.05  # Distance threshold for contact detection
    MIN_DETECTION_TIME = 0.3  # Seconds before triggering alert
    MIN_MINDFUL_CONTACT_TIME = 0.2  # Minimum contact time to count as mindful stop

    # Visual settings
    REGION_COLOR = (0, 255, 255)  # Yellow region outlines
    CONTACT_COLOR = (0, 0, 255)  # Red contact points
    HAND_COLOR = (0, 255, 0)  # Green hand landmarks

    # Available regions (can be enabled/disabled)
    AVAILABLE_REGIONS = ["scalp", "eyebrows", "eyes", "mouth", "beard"]

    # Currently active regions (overridden at startup by persisted user settings)
    ACTIVE_REGIONS = ["scalp", "eyebrows", "eyes", "mouth", "beard"]

    # Region-specific settings
    REGION_SETTINGS = {
        "scalp": {"contact_threshold": 0.05, "min_detection_time": 1.0, "alert_cooldown_time": 1.0, "show_landmarks": True},
        "eyebrows": {"contact_threshold": 0.02, "min_detection_time": 1.0, "alert_cooldown_time": 1.0, "show_landmarks": True},
        "eyes": {"contact_threshold": 0.02, "min_detection_time": 1.0, "alert_cooldown_time": 1.0, "show_landmarks": True},
        "mouth": {"contact_threshold": 0.03, "min_detection_time": 1.0, "alert_cooldown_time": 1.0, "show_landmarks": True},
        "beard": {"contact_threshold": 0.04, "min_detection_time": 1.0, "alert_cooldown_time": 1.0, "show_landmarks": True},
    }

    @classmethod
    def update_contact_duration(cls, duration: float):
        """Update min_detection_time for all regions"""
        for region in cls.REGION_SETTINGS:
            cls.REGION_SETTINGS[region]["min_detection_time"] = duration
