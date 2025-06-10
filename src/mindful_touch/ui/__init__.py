import sys
from pathlib import Path

from .detection_worker import DetectionWorker
from .qt_gui import MindfulTouchGUI, main_gui
from .settings_widget import SettingsWidget
from .status_widget import StatusWidget

__all__ = ["MindfulTouchGUI", "main_gui", "DetectionWorker", "StatusWidget", "SettingsWidget"]


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent

    return str(base_path / relative_path)


__all__.append("get_resource_path")
