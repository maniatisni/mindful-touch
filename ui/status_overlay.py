"""
Status Overlay Widget for Mindful Touch
Real-time detection status display with sound alerts
"""

import subprocess
from time import time

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatusOverlay(QWidget):
    """Simple status overlay with alert sound cooldown"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(180, 120)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 8px;
                color: white;
                font-family: monospace;
                font-size: 11px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.hands_label = QLabel("Hands: --")
        self.face_label = QLabel("Face: --")
        self.contacts_label = QLabel("Contacts: 0")
        self.alerts_label = QLabel("Status: Ready")

        for label in [self.hands_label, self.face_label, self.contacts_label, self.alerts_label]:
            layout.addWidget(label)

    def update_status(self, data):
        """Update overlay with detection data and handle alerts"""
        self.hands_label.setText(f"Hands: {'✓' if data.get('hands_detected') else '✗'}")
        self.face_label.setText(f"Face: {'✓' if data.get('face_detected') else '✗'}")

        contacts = data.get("contact_points", 0)
        self.contacts_label.setText(f"Contacts: {contacts}")

        alerts = data.get("alerts_active", [])
        if alerts:
            self.alerts_label.setText(f"ALERT: {', '.join(alerts)}")
            self.setStyleSheet(self.styleSheet() + "QLabel { color: #ff6b6b; }")
            self._play_alert_sound()
        else:
            self.alerts_label.setText("Status: OK")
            self.setStyleSheet(self.styleSheet().replace("color: #ff6b6b;", ""))

    def _play_alert_sound(self):
        """Play alert sound - spam prevention handled by contact duration"""
        subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff", "-t", "0.35"])
