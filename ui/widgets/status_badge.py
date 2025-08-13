"""
Status Badge Widget
Shows current app status with colored indicators
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from ui.styles.theme import Theme


class StatusBadge(QLabel):
    """Colored status indicator badge"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status("ready")

    def set_status(self, status):
        """Update badge status and appearance"""
        status_map = {"ready": "Ready", "detecting": "Detecting", "alert": "Alert", "error": "Error"}

        text = status_map.get(status, "Unknown")
        self.setText(text)
        self.setStyleSheet(Theme.status_badge_style(status))

        # Adjust size to content
        self.adjustSize()
        self.setMinimumHeight(32)


class AppHeader(QLabel):
    """App title with icon"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("🧘‍♀️ Mindful Touch")
        self.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_TITLE};
                font-size: {Theme.FONT_SIZE_TITLE}px;
                font-weight: 700;
                color: {Theme.TEXT_PRIMARY};
                margin: 0;
                border: none;
                background: transparent;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
