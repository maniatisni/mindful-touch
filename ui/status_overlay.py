"""
Status Overlay Widget for Mindful Touch
Real-time detection status display with sound alerts
"""

import subprocess

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class StatusOverlay(QWidget):
    """Simple status overlay with alert sound cooldown"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(200, 130)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 180);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: #e0e0e0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        self.hands_label = QLabel("Hands: --")
        self.face_label = QLabel("Face: --")
        self.contacts_label = QLabel("Contacts: 0")
        self.regions_label = QLabel("Regions: None")
        self.alerts_label = QLabel("Status: Ready")

        # Style labels for better readability
        label_style = """
            QLabel {
                color: #e0e0e0;
                font-weight: 500;
                padding: 2px 0;
            }
        """

        for label in [self.hands_label, self.face_label, self.contacts_label, self.regions_label, self.alerts_label]:
            label.setStyleSheet(label_style)
            layout.addWidget(label)

    def update_status(self, data):
        """Update overlay with detection data and handle alerts"""
        self.hands_label.setText(f"Hands: {'✓' if data.get('hands_detected') else '✗'}")
        self.face_label.setText(f"Face: {'✓' if data.get('face_detected') else '✗'}")

        contacts = data.get("contact_points", 0)
        self.contacts_label.setText(f"Contacts: {contacts}")

        # Show hierarchical region status: proximity vs alerts
        regions_with_contact = data.get("regions_with_contact", [])
        alerts = data.get("alerts_active", [])

        if alerts:
            # Red alert state - show which regions are alerting
            self.regions_label.setText(f"Regions: {', '.join(alerts)} (ALERT)")
            self.regions_label.setStyleSheet("QLabel { color: #ff6b6b; font-weight: bold; }")
            self.alerts_label.setText(f"ALERT: {', '.join(alerts)}")
            self.alerts_label.setStyleSheet("QLabel { color: #ff6b6b; font-weight: bold; }")
            self._play_alert_sound()
        elif regions_with_contact:
            # Orange proximity state - show regions with contact
            self.regions_label.setText(f"Regions: {', '.join(regions_with_contact)} (proximity)")
            self.regions_label.setStyleSheet("QLabel { color: #FF9800; font-weight: 500; }")
            self.alerts_label.setText("Status: Proximity")
            self.alerts_label.setStyleSheet("QLabel { color: #FF9800; font-weight: 500; }")
        else:
            # No contact
            self.regions_label.setText("Regions: None")
            self.regions_label.setStyleSheet("QLabel { color: #e0e0e0; font-weight: 500; }")
            self.alerts_label.setText("Status: OK")
            self.alerts_label.setStyleSheet("QLabel { color: #4CAF50; font-weight: 500; }")

    def _play_alert_sound(self):
        """Play alert sound - spam prevention handled by contact duration"""
        subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff", "-t", "0.35"])
