"""
Detection Panel - Watched regions, alert delay, and detection control
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from backend.detection.config import Config
from ui.styles.theme import Theme
from ui.widgets.toggle_switch import ToggleSwitch

REGION_LABELS = {
    "scalp": "Scalp",
    "eyebrows": "Eyebrows",
    "eyes": "Eyes",
    "mouth": "Mouth",
    "beard": "Beard area",
}


class RegionRow(QFrame):
    """One watched-region row: label left, pill toggle right"""

    toggled = pyqtSignal(bool)

    def __init__(self, label_text, last=False, parent=None):
        super().__init__(parent)
        border = "none" if last else f"1px solid {Theme.HAIRLINE}"
        self.setStyleSheet(f"""
            QFrame {{
                border: none;
                border-bottom: {border};
                background: transparent;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(Theme.ITEM_SPACING)

        label = QLabel(label_text)
        label.setStyleSheet(Theme.body_text_style())
        layout.addWidget(label)
        layout.addStretch()

        self.toggle = ToggleSwitch()
        self.toggle.toggled.connect(self.toggled.emit)
        layout.addWidget(self.toggle)

    def setChecked(self, checked):
        self.toggle.setChecked(checked)

    def isChecked(self):
        return self.toggle.isChecked()


class DetectionPanel(QWidget):
    """Right panel: watched regions, alert delay, detection control"""

    region_toggled = pyqtSignal(str, bool)
    contact_duration_changed = pyqtSignal(float)
    detection_button_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.region_toggles = {}
        self.is_detecting = False
        self.setup_ui()

    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QWidget()
        card.setObjectName("regionsCard")
        card.setStyleSheet(f"""
            QWidget#regionsCard {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """)
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING)
        layout.setSpacing(0)

        # Section label + helper line
        title = QLabel("Watched regions")
        title.setStyleSheet(Theme.section_title_style())
        layout.addWidget(title)
        layout.addSpacing(4)

        helper = QLabel("Choose where a lingering touch counts.")
        helper.setStyleSheet(Theme.helper_text_style())
        layout.addWidget(helper)
        layout.addSpacing(10)

        # Region rows
        regions = Config.AVAILABLE_REGIONS
        for i, region in enumerate(regions):
            row = RegionRow(REGION_LABELS.get(region, region.title()), last=(i == len(regions) - 1))
            row.setChecked(region in Config.ACTIVE_REGIONS)
            row.toggled.connect(lambda checked, r=region: self.region_toggled.emit(r, checked))
            self.region_toggles[region] = row
            layout.addWidget(row)

        layout.addStretch()

        # Divider above alert delay
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {Theme.BORDER}; border: none;")
        layout.addWidget(divider)
        layout.addSpacing(16)

        # Alert delay
        delay_title = QLabel("Alert delay")
        delay_title.setStyleSheet(Theme.section_title_style())
        layout.addWidget(delay_title)
        layout.addSpacing(10)

        delay_row = QHBoxLayout()
        delay_row.setSpacing(12)

        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(5, 100)  # 0.5s to 10.0s (x10)
        self.delay_slider.setValue(10)
        self.delay_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self.delay_slider.setStyleSheet(f"""
            QSlider {{
                border: none;
                background: transparent;
                height: 20px;
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: {Theme.BORDER};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.PRIMARY};
                border: 3px solid {Theme.SURFACE};
                width: 14px;
                height: 14px;
                margin: -8px 0;
                border-radius: 10px;
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.PRIMARY};
                border-radius: 2px;
            }}
        """)
        self.delay_slider.valueChanged.connect(self._on_delay_changed)
        delay_row.addWidget(self.delay_slider)

        self.delay_value_label = QLabel("1.0s")
        self.delay_value_label.setMinimumWidth(40)
        self.delay_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.delay_value_label.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: 13px;
                color: {Theme.INK_SOFT};
                border: none;
                background: transparent;
            }}
        """)
        delay_row.addWidget(self.delay_value_label)

        layout.addLayout(delay_row)
        layout.addSpacing(20)

        # Detection control button
        self.detection_button = QPushButton("Start detection")
        self.detection_button.setStyleSheet(Theme.button_primary_style())
        self.detection_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.detection_button.clicked.connect(self.detection_button_clicked.emit)
        layout.addWidget(self.detection_button)

    def _on_delay_changed(self, value):
        """Handle slider value change"""
        duration = value / 10.0
        self.delay_value_label.setText(f"{duration:.1f}s")
        self.contact_duration_changed.emit(duration)

    def set_contact_duration(self, duration):
        """Set slider value"""
        self.delay_slider.setValue(int(duration * 10))
        self.delay_value_label.setText(f"{duration:.1f}s")

    def set_detection_state(self, detecting):
        """Switch the control button between start (primary) and pause (outlined clay)"""
        self.is_detecting = detecting
        if detecting:
            self.detection_button.setText("Pause detection")
            self.detection_button.setStyleSheet(Theme.button_pause_style())
        else:
            self.detection_button.setText("Start detection")
            self.detection_button.setStyleSheet(Theme.button_primary_style())

    def set_button_enabled(self, enabled):
        """Enable/disable the detection button during transitions"""
        self.detection_button.setEnabled(enabled)

    def update_region_state(self, region, active):
        """Update region toggle state (for external changes)"""
        if region in self.region_toggles:
            self.region_toggles[region].setChecked(active)
