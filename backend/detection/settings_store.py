"""
Settings persistence for Mindful Touch
Simple JSON file store in the user's home directory
"""

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".mindful-touch" / "settings.json"

DEFAULTS = {
    "active_regions": ["scalp", "eyebrows", "eyes", "mouth", "beard"],
    "alert_delay": 1.0,
}


def load() -> dict:
    """Load settings from disk, falling back to defaults on any error"""
    try:
        if SETTINGS_PATH.exists():
            return {**DEFAULTS, **json.loads(SETTINGS_PATH.read_text())}
    except Exception as e:
        print(f"Could not load settings, using defaults: {e}")
    return DEFAULTS.copy()


def save(settings: dict):
    """Save settings to disk, silently ignoring write errors"""
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(settings, indent=2))
    except Exception as e:
        print(f"Could not save settings: {e}")
