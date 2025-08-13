"""
Camera Panel - Right side display
Live detection feed and activity stats
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QHBoxLayout, QPushButton

from ui.styles.theme import Theme


class LiveDetectionCard(QWidget):
    """Card for camera feed and controls"""
    
    start_detection = pyqtSignal()
    stop_detection = pyqtSignal()
    toggle_privacy = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_detecting = False
        self.show_feed = True
        self.setup_ui()
        self.setStyleSheet(Theme.card_style())
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING)
        layout.setSpacing(Theme.ITEM_SPACING)
        
        # Title
        title = QLabel("Live Detection")
        title.setStyleSheet(Theme.section_title_style())
        layout.addWidget(title)
        
        # Camera container
        self.camera_container = QWidget()
        self.camera_container.setMinimumSize(720, 540)  # 4:3 aspect ratio
        container_layout = QVBoxLayout(self.camera_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(720, 540)
        self.camera_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: {Theme.BORDER_RADIUS}px;
                color: {Theme.TEXT_SECONDARY};
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
            }}
        """)
        
        # Default message
        self._set_default_message()
        container_layout.addWidget(self.camera_label)
        layout.addWidget(self.camera_container)
        
        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(Theme.ITEM_SPACING)
        
        # Detection button
        self.detection_button = QPushButton("Start Detection")
        self.detection_button.setStyleSheet(Theme.button_primary_style())
        self.detection_button.clicked.connect(self._on_detection_button_clicked)
        
        # Privacy button
        self.privacy_button = QPushButton("Hide Feed")
        self.privacy_button.setEnabled(False)
        self.privacy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT_ORANGE};
                color: {Theme.TEXT_LIGHT};
                border: none;
                border-radius: 12px;
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                font-weight: 600;
                padding: 12px 24px;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 152, 0, 0.9);
            }}
            QPushButton:disabled {{
                background-color: {Theme.TEXT_MUTED};
                color: rgba(255, 255, 255, 0.6);
            }}
        """)
        self.privacy_button.clicked.connect(self._on_privacy_button_clicked)
        
        controls_layout.addWidget(self.detection_button)
        controls_layout.addWidget(self.privacy_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def _set_default_message(self):
        """Set default camera message"""
        self.camera_label.setText("📷 Camera Preview\n\nClick 'Start Detection' to begin\nmonitoring facial touch patterns")
    
    def _on_detection_button_clicked(self):
        """Handle detection button click"""
        if not self.is_detecting:
            self.start_detection.emit()
        else:
            self.stop_detection.emit()
    
    def _on_privacy_button_clicked(self):
        """Handle privacy button click"""
        self.toggle_privacy.emit()
    
    def set_detection_state(self, detecting):
        """Update UI for detection state"""
        self.is_detecting = detecting
        
        if detecting:
            self.detection_button.setText("Stop Detection")
            self.detection_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ACCENT_RED};
                    color: {Theme.TEXT_LIGHT};
                    border: none;
                    border-radius: 12px;
                    font-family: {Theme.FONT_BODY};
                    font-size: {Theme.FONT_SIZE_BODY}px;
                    font-weight: 600;
                    padding: 12px 24px;
                    min-height: 44px;
                }}
                QPushButton:hover {{
                    background-color: rgba(231, 76, 60, 0.9);
                }}
            """)
            self.privacy_button.setEnabled(True)
        else:
            self.detection_button.setText("Start Detection")
            self.detection_button.setStyleSheet(Theme.button_primary_style())
            self.privacy_button.setEnabled(False)
            self.privacy_button.setText("Hide Feed")
            self.show_feed = True
            self._set_default_message()
    
    def set_privacy_state(self, show_feed):
        """Update UI for privacy state"""
        self.show_feed = show_feed
        
        if show_feed:
            self.privacy_button.setText("Hide Feed")
            self.privacy_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.ACCENT_ORANGE};
                    color: {Theme.TEXT_LIGHT};
                    border: none;
                    border-radius: 12px;
                    font-family: {Theme.FONT_BODY};
                    font-size: {Theme.FONT_SIZE_BODY}px;
                    font-weight: 600;
                    padding: 12px 24px;
                    min-height: 44px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 152, 0, 0.9);
                }}
            """)
        else:
            self.privacy_button.setText("Show Feed")
            self.privacy_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Theme.TEXT_SECONDARY};
                    color: {Theme.TEXT_LIGHT};
                    border: none;
                    border-radius: 12px;
                    font-family: {Theme.FONT_BODY};
                    font-size: {Theme.FONT_SIZE_BODY}px;
                    font-weight: 600;
                    padding: 12px 24px;
                    min-height: 44px;
                }}
                QPushButton:hover {{
                    background-color: rgba(96, 125, 139, 0.9);
                }}
            """)
            self.camera_label.setText("🔒 Privacy Mode Active\n\nDetection running in background\nClick 'Show Feed' to view camera")
    
    def update_camera_frame(self, pixmap):
        """Update camera display with new frame"""
        if self.show_feed:
            self.camera_label.setPixmap(pixmap)


class ActivityCard(QWidget):
    """Card for session statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setStyleSheet(Theme.card_style())
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING, Theme.CARD_PADDING)
        layout.setSpacing(Theme.ITEM_SPACING)
        
        # Title
        title = QLabel("Today's Activity")
        title.setStyleSheet(Theme.section_title_style())
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(Theme.SECTION_SPACING)
        
        # Detections counter
        self.detections_widget = self._create_stat_widget("0", "DETECTIONS", Theme.ACCENT_BLUE)
        stats_layout.addWidget(self.detections_widget)
        
        # Session timer
        self.session_widget = self._create_stat_widget("0m", "SESSION", Theme.ACCENT_BLUE)
        stats_layout.addWidget(self.session_widget)
        
        # Mindful stops (placeholder)
        self.stops_widget = self._create_stat_widget("0", "MINDFUL STOPS", Theme.TEXT_MUTED)
        stats_layout.addWidget(self.stops_widget)
        
        layout.addLayout(stats_layout)
    
    def _create_stat_widget(self, value, label, color):
        """Create a stat display widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(4)
        
        # Value (big number)
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_TITLE};
                font-size: 36px;
                font-weight: 700;
                color: {color};
                margin: 0;
                border: none;
                background: transparent;
            }}
        """)
        
        # Label (small text)
        text_label = QLabel(label)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_SMALL}px;
                font-weight: 600;
                color: {Theme.TEXT_SECONDARY};
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0;
                border: none;
                background: transparent;
            }}
        """)
        
        layout.addWidget(value_label)
        layout.addWidget(text_label)
        
        # Store references for updates
        widget.value_label = value_label
        widget.text_label = text_label
        
        return widget
    
    def update_detections(self, count):
        """Update detections counter"""
        self.detections_widget.value_label.setText(str(count))
    
    def update_session_time(self, minutes):
        """Update session timer"""
        if minutes < 60:
            text = f"{minutes}m"
        else:
            hours = minutes // 60
            mins = minutes % 60
            text = f"{hours}h {mins}m"
        self.session_widget.value_label.setText(text)
    
    def update_mindful_stops(self, count):
        """Update mindful stops counter (placeholder)"""
        self.stops_widget.value_label.setText(str(count))


class CameraPanel(QWidget):
    """Right panel containing camera feed and stats"""
    
    start_detection = pyqtSignal()
    stop_detection = pyqtSignal()
    toggle_privacy = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Theme.CARD_MARGIN)
        
        # Live detection card
        self.detection_card = LiveDetectionCard()
        self.detection_card.start_detection.connect(self.start_detection.emit)
        self.detection_card.stop_detection.connect(self.stop_detection.emit)
        self.detection_card.toggle_privacy.connect(self.toggle_privacy.emit)
        layout.addWidget(self.detection_card)
        
        # Activity card
        self.activity_card = ActivityCard()
        layout.addWidget(self.activity_card)
        
        # Stretch to push cards to top
        layout.addStretch()
    
    def set_detection_state(self, detecting):
        """Update detection state"""
        self.detection_card.set_detection_state(detecting)
    
    def set_privacy_state(self, show_feed):
        """Update privacy state"""
        self.detection_card.set_privacy_state(show_feed)
    
    def update_camera_frame(self, pixmap):
        """Update camera frame"""
        self.detection_card.update_camera_frame(pixmap)
    
    def update_stats(self, detections, session_minutes, mindful_stops):
        """Update activity statistics"""
        self.activity_card.update_detections(detections)
        self.activity_card.update_session_time(session_minutes)
        self.activity_card.update_mindful_stops(mindful_stops)