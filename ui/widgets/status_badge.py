"""
Status Badge Widget
Soft status pill and app header with the logo mark
"""

from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ui.styles.theme import LOGO_SVG, Theme


class StatusBadge(QLabel):
    """Soft colored status pill"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status("ready")

    def set_status(self, status):
        """Update badge status and appearance"""
        status_map = {"ready": "Ready", "detecting": "Detecting", "alert": "Touch noticed", "error": "Error"}

        text = status_map.get(status, "Unknown")
        self.setText(text)
        self.setStyleSheet(Theme.status_badge_style(status))

        # Adjust size to content
        self.adjustSize()
        self.setMinimumHeight(28)


class LogoMark(QSvgWidget):
    """The Mindful Touch mark: cup in dusty blue, heart in clay"""

    def __init__(self, size=20, parent=None):
        super().__init__(parent)
        self.load(LOGO_SVG.encode())
        self.setFixedSize(size, size)
        self.setStyleSheet("background: transparent; border: none;")


class AppHeader(QWidget):
    """Logo mark + wordmark"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(LogoMark(20))

        wordmark = QLabel("Mindful Touch")
        wordmark.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_TITLE};
                font-size: {Theme.FONT_SIZE_TITLE}px;
                font-weight: 700;
                color: {Theme.INK};
                border: none;
                background: transparent;
            }}
        """)
        layout.addWidget(wordmark)
