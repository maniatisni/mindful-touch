"""Basic tests for Mindful Touch PyQt6 app"""


def test_imports():
    """Test that all core modules can be imported"""
    assert True


def test_config_values():
    """Test basic config values"""
    from backend.detection.config import Config

    assert len(Config.AVAILABLE_REGIONS) > 0
    assert "scalp" in Config.AVAILABLE_REGIONS
    assert Config.CAMERA_WIDTH > 0
