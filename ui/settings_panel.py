"""
Settings Panel Widget for Mindful Touch
Modular UI component for region toggles and alert controls
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QDoubleSpinBox, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from backend.detection.config import Config


class SettingsPanel(QWidget):
    """Modular settings panel for region toggles and alert controls"""

    region_toggled = pyqtSignal(str, bool)
    contact_duration_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.contact_duration = 1.0  # Default 1 second
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # Detection Regions Group
        regions_group = QGroupBox("Detection Regions")
        regions_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 8px;
                margin: 5px 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        regions_layout = QVBoxLayout(regions_group)

        self.region_checkboxes = {}
        for region in Config.AVAILABLE_REGIONS:
            checkbox = QCheckBox(region.title())
            checkbox.setChecked(region in Config.ACTIVE_REGIONS)
            checkbox.toggled.connect(lambda checked, r=region: self.region_toggled.emit(r, checked))
            checkbox.setStyleSheet("""
                QCheckBox {
                    font-size: 12px;
                    padding: 3px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
            """)
            regions_layout.addWidget(checkbox)
            self.region_checkboxes[region] = checkbox

        layout.addWidget(regions_group)

        # Alert Settings Group
        alert_group = QGroupBox("Alert Settings")
        alert_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ccc;
                border-radius: 8px;
                margin: 5px 0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        alert_layout = QVBoxLayout(alert_group)

        delay_layout = QHBoxLayout()
        duration_label = QLabel("Contact Duration (s):")
        duration_label.setStyleSheet("font-size: 12px;")
        delay_layout.addWidget(duration_label)

        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setRange(0.5, 10.0)
        self.duration_spinbox.setSingleStep(0.5)
        self.duration_spinbox.setDecimals(1)
        self.duration_spinbox.setValue(self.contact_duration)
        self.duration_spinbox.valueChanged.connect(lambda v: self.contact_duration_changed.emit(float(v)))
        self.duration_spinbox.setStyleSheet("""
            QDoubleSpinBox {
                font-size: 12px;
                padding: 3px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        delay_layout.addWidget(self.duration_spinbox)

        alert_layout.addLayout(delay_layout)
        layout.addWidget(alert_group)

        layout.addStretch()

    def update_region_state(self, region: str, active: bool):
        """Update checkbox state (for external changes)"""
        if region in self.region_checkboxes:
            self.region_checkboxes[region].setChecked(active)

    def get_contact_duration(self) -> float:
        """Get current contact duration value"""
        return self.contact_duration

    def set_contact_duration(self, duration: float):
        """Set contact duration value"""
        self.contact_duration = duration
        self.duration_spinbox.setValue(duration)
