"""Basic tests for Mindful Touch PyQt6 app"""

def test_imports():
    """Test that all core modules can be imported"""
    import PyQt6.QtWidgets
    import cv2
    import mediapipe as mp
    import numpy as np
    from backend.detection.config import Config
    from backend.detection.multi_region_detector import MultiRegionDetector
    from ui.status_overlay import StatusOverlay
    from ui.settings_panel import SettingsPanel
    assert True

def test_config_values():
    """Test basic config values"""
    from backend.detection.config import Config
    assert len(Config.AVAILABLE_REGIONS) > 0
    assert "scalp" in Config.AVAILABLE_REGIONS
    assert Config.CAMERA_WIDTH > 0