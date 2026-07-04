"""
Camera Panel - live feed with session stats inside one surface card
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ui.styles.theme import Theme


class StatBlock(QWidget):
    """Big number over a muted caption"""

    def __init__(self, value, caption, value_color=None, parent=None):
        super().__init__(parent)
        self.value_color = value_color or Theme.INK
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(self._value_style(self.value_color))
        layout.addWidget(self.value_label)

        caption_label = QLabel(caption)
        caption_label.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: 12px;
                color: {Theme.MUTED};
                border: none;
                background: transparent;
            }}
        """)
        layout.addWidget(caption_label)

    @staticmethod
    def _value_style(color):
        return f"""
            QLabel {{
                font-family: {Theme.FONT_TITLE};
                font-size: 22px;
                font-weight: 700;
                color: {color};
                border: none;
                background: transparent;
            }}
        """

    def set_value(self, text):
        self.value_label.setText(text)

    def flash(self, color, duration_ms=1500):
        """Briefly recolor the value, then restore"""
        self.value_label.setStyleSheet(self._value_style(color))
        QTimer.singleShot(duration_ms, lambda: self.value_label.setStyleSheet(self._value_style(self.value_color)))


class CameraPanel(QWidget):
    """Left panel: camera feed card with stats row"""

    toggle_privacy = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_detecting = False
        self.show_feed = True
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QWidget()
        card.setObjectName("cameraCard")
        card.setStyleSheet(f"""
            QWidget#cameraCard {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Header row: label left, hide-feed button right
        header_row = QHBoxLayout()
        header_row.setSpacing(Theme.ITEM_SPACING)

        title = QLabel("Camera")
        title.setStyleSheet(Theme.section_title_style())
        header_row.addWidget(title)
        header_row.addStretch()

        self.privacy_button = QPushButton("Hide feed")
        self.privacy_button.setEnabled(False)
        self.privacy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.privacy_button.setStyleSheet(self._privacy_button_style())
        self.privacy_button.clicked.connect(self.toggle_privacy.emit)
        header_row.addWidget(self.privacy_button)

        layout.addLayout(header_row)
        layout.addSpacing(14)

        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(480, 320)
        self.camera_label.setStyleSheet(f"""
            QLabel {{
                background-color: {Theme.FEED_BG};
                border: none;
                border-radius: 12px;
                color: {Theme.INK_SOFT};
                font-family: {Theme.FONT_BODY};
                font-size: 14px;
            }}
        """)
        self._set_default_message()
        layout.addWidget(self.camera_label, stretch=1)
        layout.addSpacing(18)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(Theme.SECTION_SPACING)

        self.session_stat = StatBlock("00:00:00", "Session")
        stats_row.addWidget(self.session_stat)

        self.touches_stat = StatBlock("0", "Touches noticed")
        stats_row.addWidget(self.touches_stat)

        self.stops_stat = StatBlock("0", "Mindful stops", value_color=Theme.SAGE)
        stats_row.addWidget(self.stops_stat)

        stats_row.addStretch()
        layout.addLayout(stats_row)

    @staticmethod
    def _privacy_button_style():
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.INK_SOFT};
                border: 1px solid {Theme.BORDER};
                border-radius: 13px;
                font-family: {Theme.FONT_BODY};
                font-size: 12px;
                font-weight: 600;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                border-color: {Theme.PRIMARY};
                color: {Theme.PRIMARY};
            }}
            QPushButton:disabled {{
                color: {Theme.TOGGLE_OFF};
                border-color: {Theme.HAIRLINE};
            }}
        """

    def _set_default_message(self):
        """Set default camera message"""
        self.camera_label.setText(
            "Camera preview\n\nPress  Start detection  to begin.\n\nPosition yourself so your face\nis clearly visible in the frame."
        )

    def set_detection_state(self, detecting):
        """Update UI for detection state"""
        self.is_detecting = detecting
        self.privacy_button.setEnabled(detecting)
        if not detecting:
            self.privacy_button.setText("Hide feed")
            self.show_feed = True
            self._set_default_message()

    def set_privacy_state(self, show_feed):
        """Update UI for privacy state"""
        self.show_feed = show_feed

        if show_feed:
            self.privacy_button.setText("Hide feed")
        else:
            self.privacy_button.setText("Show feed")
            self.camera_label.setText("Privacy mode\n\nDetection keeps running in the background.\nPress  Show feed  to view the camera.")

    def update_camera_frame(self, pixmap):
        """Update camera display with new frame"""
        if self.show_feed:
            self.camera_label.setPixmap(pixmap)

    def update_stats(self, detections, session_seconds, mindful_stops):
        """Update the stats row"""
        hours, rem = divmod(int(session_seconds), 3600)
        minutes, seconds = divmod(rem, 60)
        self.session_stat.set_value(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.touches_stat.set_value(str(detections))
        self.stops_stat.set_value(str(mindful_stops))

    def show_mindful_stop_flash(self):
        """Briefly highlight the mindful stops stat"""
        self.stops_stat.flash(Theme.SAGE_HOVER)
