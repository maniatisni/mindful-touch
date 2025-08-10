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

        # Separate lines within same box
        self.detection_label = QLabel("👋❌")
        self.contacts_label = QLabel("Contacts: 0")
        self.status_label = QLabel("Status: Ready")

        # Style labels for better readability
        label_style = """
            QLabel {
                color: #e0e0e0;
                font-weight: 500;
                padding: 2px 0;
            }
        """

        for label in [self.detection_label, self.contacts_label, self.status_label]:
            label.setStyleSheet(label_style)
            layout.addWidget(label)

    def update_status(self, data):
        """Update overlay with detection data and handle alerts"""
        # Update separate lines
        hands_icon = "👋" if data.get("hands_detected") else "❌"
        face_icon = "👤" if data.get("face_detected") else "❌"
        contacts = data.get("contact_points", 0)

        # Show hierarchical region status
        regions_with_contact = data.get("regions_with_contact", [])
        alerts = data.get("alerts_active", [])

        if alerts:
            status_text = f"{', '.join(alerts)} ALERT"
            status_color = "#ff6b6b"
            self._play_alert_sound()
        elif regions_with_contact:
            status_text = f"{', '.join(regions_with_contact)} proximity"
            status_color = "#FF9800"
        else:
            status_text = "monitoring"
            status_color = "#4CAF50"

        # Update individual lines
        self.detection_label.setText(f"{hands_icon} {face_icon}")
        self.contacts_label.setText(f"Contacts: {contacts}")
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(f"QLabel {{ color: {status_color}; font-weight: 500; padding: 2px 0; }}")

    def _play_alert_sound(self):
        """Play alert sound - spam prevention handled by contact duration"""
        subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff", "-t", "0.35"])
