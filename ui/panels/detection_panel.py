"""
Detection Panel - Left side controls
Region toggles and notification settings
"""

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QSlider, QHBoxLayout

from backend.detection.config import Config
from ui.styles.theme import Theme
from ui.widgets.toggle_switch import LabeledToggle


class DetectionRegionsCard(QWidget):
    """Card for region toggle controls"""
    
    region_toggled = pyqtSignal(str, bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.region_toggles = {}
        self.setup_ui()
        self.setStyleSheet(Theme.card_style())
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING)
        layout.setSpacing(Theme.ITEM_SPACING)
        
        # Title
        title = QLabel("Detection Regions")
        title.setStyleSheet(Theme.section_title_style())
        layout.addWidget(title)
        
        # Region toggles
        for region in Config.AVAILABLE_REGIONS:
            toggle = LabeledToggle(region.title())
            toggle.setChecked(region in Config.ACTIVE_REGIONS)
            toggle.toggled.connect(lambda checked, r=region: self.region_toggled.emit(r, checked))
            
            self.region_toggles[region] = toggle
            layout.addWidget(toggle)
    
    def update_region_state(self, region, active):
        """Update toggle state (for external changes)"""
        if region in self.region_toggles:
            self.region_toggles[region].setChecked(active)


class NotificationSettingsCard(QWidget):
    """Card for notification settings"""
    
    contact_duration_changed = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setStyleSheet(Theme.card_style())
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING)
        layout.setSpacing(Theme.ITEM_SPACING)
        
        # Title
        title = QLabel("Notification Settings")
        title.setStyleSheet(Theme.section_title_style())
        layout.addWidget(title)
        
        # Alert delay section
        delay_layout = QVBoxLayout()
        delay_layout.setSpacing(8)
        
        # Delay label with value
        delay_header = QHBoxLayout()
        delay_label = QLabel("Alert Delay:")
        delay_label.setStyleSheet(Theme.body_text_style() + """
            QLabel {
                border: none;
                background: transparent;
            }
        """)
        
        self.delay_value_label = QLabel("1.0s")
        self.delay_value_label.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                font-weight: 600;
                color: {Theme.ACCENT_BLUE};
                border: none;
                background: transparent;
            }}
        """)
        
        delay_header.addWidget(delay_label)
        delay_header.addStretch()
        delay_header.addWidget(self.delay_value_label)
        delay_layout.addLayout(delay_header)
        
        # Slider
        self.delay_slider = QSlider()
        self.delay_slider.setOrientation(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(5, 100)   # 0.5s to 10.0s (×10)
        self.delay_slider.setValue(10)       # 1.0s default
        self.delay_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.delay_slider.setTickInterval(25)  # Every 2.5s
        
        self.delay_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {Theme.CARD_BORDER};
                height: 6px;
                background: {Theme.TOGGLE_BACKGROUND};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {Theme.ACCENT_BLUE};
                border: 2px solid {Theme.TEXT_LIGHT};
                width: 20px;
                height: 20px;
                margin: -8px 0;
                border-radius: 12px;
            }}
            QSlider::handle:horizontal:hover {{
                background: rgba(52, 152, 219, 0.8);
            }}
            QSlider::sub-page:horizontal {{
                background: {Theme.ACCENT_BLUE};
                border-radius: 3px;
            }}
        """)
        
        self.delay_slider.valueChanged.connect(self._on_delay_changed)
        delay_layout.addWidget(self.delay_slider)
        
        layout.addLayout(delay_layout)
    
    def _on_delay_changed(self, value):
        """Handle slider value change"""
        duration = value / 10.0  # Convert back to seconds
        self.delay_value_label.setText(f"{duration:.1f}s")
        self.contact_duration_changed.emit(duration)
    
    def set_contact_duration(self, duration):
        """Set slider value"""
        self.delay_slider.setValue(int(duration * 10))
        self.delay_value_label.setText(f"{duration:.1f}s")


class DetectionPanel(QWidget):
    """Left panel containing detection controls"""
    
    region_toggled = pyqtSignal(str, bool)
    contact_duration_changed = pyqtSignal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Theme.CARD_MARGIN)
        
        # Detection regions card
        self.regions_card = DetectionRegionsCard()
        self.regions_card.region_toggled.connect(self.region_toggled.emit)
        layout.addWidget(self.regions_card)
        
        # Notification settings card
        self.settings_card = NotificationSettingsCard()
        self.settings_card.contact_duration_changed.connect(self.contact_duration_changed.emit)
        layout.addWidget(self.settings_card)
        
        # Stretch to push cards to top
        layout.addStretch()
    
    def update_region_state(self, region, active):
        """Update region toggle state"""
        self.regions_card.update_region_state(region, active)
    
    def set_contact_duration(self, duration):
        """Set contact duration slider"""
        self.settings_card.set_contact_duration(duration)