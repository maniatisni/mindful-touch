"""Basic tests for Mindful Touch PyQt6 app"""


def test_imports():
    """Test that all core modules can be imported"""
    from backend.detection import settings_store
    from backend.detection.config import Config
    from backend.detection.multi_region_detector import MultiRegionDetector
    from ui.panels.camera_panel import CameraPanel
    from ui.panels.detection_panel import DetectionPanel
    from ui.styles.theme import Theme

    assert Config is not None
    assert MultiRegionDetector is not None
    assert CameraPanel is not None
    assert DetectionPanel is not None
    assert Theme is not None
    assert settings_store is not None


def test_config_values():
    """Test basic config values"""
    from backend.detection.config import Config

    assert Config.AVAILABLE_REGIONS == ["scalp", "eyebrows", "eyes", "mouth", "beard"]
    assert set(Config.ACTIVE_REGIONS) <= set(Config.AVAILABLE_REGIONS)
    assert Config.CAMERA_WIDTH > 0
    assert set(Config.REGION_SETTINGS.keys()) == set(Config.AVAILABLE_REGIONS)


def test_settings_store_defaults(tmp_path, monkeypatch):
    """Settings store falls back to defaults and round-trips saves"""
    from backend.detection import settings_store

    monkeypatch.setattr(settings_store, "SETTINGS_PATH", tmp_path / "settings.json")

    settings = settings_store.load()
    assert settings == settings_store.DEFAULTS

    settings["alert_delay"] = 2.5
    settings["active_regions"] = ["mouth"]
    settings_store.save(settings)

    reloaded = settings_store.load()
    assert reloaded["alert_delay"] == 2.5
    assert reloaded["active_regions"] == ["mouth"]
