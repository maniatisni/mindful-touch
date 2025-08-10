"""Main application window for Mindful Touch PyQt GUI."""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QPushButton, QFrame, QSlider, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from .widgets.custom_toggle import ToggleRow
from .widgets.camera_display import CameraDisplayWidget
from .widgets.detection_worker import DetectionWorker
from backend.audio.sound_manager import SoundManager


class HeaderWidget(QFrame):
    """Header widget with logo, title, and connection status."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(80)
        self.setObjectName("headerWidget")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Logo placeholder (40x40px)
        logo = QLabel("📱")
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
                color: white;
                font-size: 20px;
            }
        """)
        
        # Title
        title = QLabel("Mindful Touch")
        title.setFont(QFont("-apple-system", 24, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #4a5568; margin-left: 15px;")
        
        # Connection status
        self.status_label = QLabel("Offline")
        self.status_label.setStyleSheet("""
            QLabel {
                background: #cbd5e0;
                color: #4a5568;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        
        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.status_label)
        
    def set_connected(self, connected: bool):
        """Update connection status display."""
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("""
                QLabel {
                    background: #10b981;
                    color: white;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
            """)
        else:
            self.status_label.setText("Offline")
            self.status_label.setStyleSheet("""
                QLabel {
                    background: #cbd5e0;
                    color: #4a5568;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                }
            """)


class ControlsPanel(QFrame):
    """Left panel containing detection controls and notification settings."""
    
    region_toggled = pyqtSignal(str, bool)
    notification_settings_changed = pyqtSignal(dict)
    test_sound_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.region_toggles = {}
        self.notification_settings = {
            'enabled': True,
            'sound': True,
            'delay': 3,
            'sound_type': 'Chime'
        }
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("controlsPanel")
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)
        
        # Detection Regions section
        regions_label = QLabel("Detection Regions")
        regions_label.setFont(QFont("-apple-system", 16, QFont.Weight.DemiBold))
        regions_label.setStyleSheet("color: #4a5568; margin-bottom: 10px;")
        layout.addWidget(regions_label)
        
        # Region toggles
        regions = [
            ("Scalp", True),      # Default ON
            ("Eyebrows", False),  # Default OFF
            ("Eyes", False),      # Default OFF
            ("Mouth", False),     # Default OFF
            ("Beard", False)      # Default OFF
        ]
        
        for region_name, default_state in regions:
            toggle_row = ToggleRow(region_name, default_state)
            toggle_row.toggled.connect(self.on_region_toggled)
            self.region_toggles[region_name] = toggle_row
            layout.addWidget(toggle_row)
        
        layout.addSpacing(15)
        
        # Notification Settings section
        notifications_label = QLabel("Notification Settings")
        notifications_label.setFont(QFont("-apple-system", 16, QFont.Weight.DemiBold))
        notifications_label.setStyleSheet("color: #4a5568; margin-bottom: 10px;")
        layout.addWidget(notifications_label)
        
        # Enable notifications toggle
        self.notifications_toggle = ToggleRow("Enable notifications", True)
        self.notifications_toggle.toggled.connect(self.on_notifications_toggled)
        layout.addWidget(self.notifications_toggle)
        
        # Sound alerts toggle
        self.sound_toggle = ToggleRow("Sound alerts", True)
        self.sound_toggle.toggled.connect(self.on_sound_toggled)
        layout.addWidget(self.sound_toggle)
        
        # Alert delay slider
        delay_container = QWidget()
        delay_layout = QVBoxLayout(delay_container)
        delay_layout.setContentsMargins(12, 8, 12, 8)
        delay_layout.setSpacing(8)
        
        delay_header = QHBoxLayout()
        delay_label = QLabel("Alert delay:")
        delay_label.setStyleSheet("color: #4a5568; font-size: 14px; font-weight: 500;")
        
        self.delay_value_label = QLabel("3s")
        self.delay_value_label.setStyleSheet("color: #667eea; font-size: 14px; font-weight: 600;")
        
        delay_header.addWidget(delay_label)
        delay_header.addStretch()
        delay_header.addWidget(self.delay_value_label)
        
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(10)
        self.delay_slider.setValue(3)
        self.delay_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: #cbd5e0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #667eea;
                border: none;
                width: 20px;
                height: 20px;
                border-radius: 10px;
                margin: -7px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #5a67d8;
            }
        """)
        self.delay_slider.valueChanged.connect(self.on_delay_changed)
        
        delay_layout.addLayout(delay_header)
        delay_layout.addWidget(self.delay_slider)
        layout.addWidget(delay_container)
        
        # Sound selection buttons
        sound_container = QWidget()
        sound_layout = QVBoxLayout(sound_container)
        sound_layout.setContentsMargins(12, 8, 12, 8)
        sound_layout.setSpacing(10)
        
        sound_label = QLabel("Sound type:")
        sound_label.setStyleSheet("color: #4a5568; font-size: 14px; font-weight: 500;")
        sound_layout.addWidget(sound_label)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.sound_button_group = QButtonGroup()
        sound_types = ["🔔 Chime", "📢 Beep", "🎵 Gentle"]
        
        for i, sound_type in enumerate(sound_types):
            button = QPushButton(sound_type)
            button.setCheckable(True)
            button.setFixedHeight(36)
            button.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    padding: 6px 12px;
                    font-size: 13px;
                    color: #4a5568;
                }
                QPushButton:checked {
                    background: #667eea;
                    border-color: #667eea;
                    color: white;
                }
                QPushButton:hover {
                    border-color: #667eea;
                    transform: translateY(-1px);
                }
            """)
            
            if i == 0:  # Default to Chime
                button.setChecked(True)
            
            button.clicked.connect(lambda checked, sound=sound_type.split()[1]: self.on_sound_type_changed(sound))
            self.sound_button_group.addButton(button, i)
            buttons_layout.addWidget(button)
        
        sound_layout.addLayout(buttons_layout)
        layout.addWidget(sound_container)
        
        # Test sound button
        self.test_button = QPushButton("▶️ Test Sound")
        self.test_button.setFixedHeight(40)
        self.test_button.setStyleSheet("""
            QPushButton {
                background: white;
                border: 2px solid #10b981;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
                color: #10b981;
                margin: 0 12px;
            }
            QPushButton:hover {
                background: #10b981;
                color: white;
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                transform: translateY(0px);
            }
        """)
        self.test_button.clicked.connect(self.test_sound_requested.emit)
        layout.addWidget(self.test_button)
        
        layout.addStretch()
        
    def on_region_toggled(self, region: str, enabled: bool):
        """Handle region toggle changes."""
        self.region_toggled.emit(region, enabled)
        
    def on_notifications_toggled(self, region: str, enabled: bool):
        """Handle notifications toggle."""
        self.notification_settings['enabled'] = enabled
        self.notification_settings_changed.emit(self.notification_settings)
        
    def on_sound_toggled(self, region: str, enabled: bool):
        """Handle sound toggle."""
        self.notification_settings['sound'] = enabled
        self.notification_settings_changed.emit(self.notification_settings)
        
    def on_delay_changed(self, value: int):
        """Handle delay slider changes."""
        self.delay_value_label.setText(f"{value}s")
        self.notification_settings['delay'] = value
        self.notification_settings_changed.emit(self.notification_settings)
        
    def on_sound_type_changed(self, sound_type: str):
        """Handle sound type selection."""
        self.notification_settings['sound_type'] = sound_type
        self.notification_settings_changed.emit(self.notification_settings)
        
    def get_enabled_regions(self):
        """Get list of currently enabled regions."""
        return [name for name, toggle in self.region_toggles.items() if toggle.is_checked()]
        
    def get_notification_settings(self):
        """Get current notification settings."""
        return self.notification_settings.copy()


class CameraPanel(QFrame):
    """Center panel containing camera display and start/stop controls."""
    
    detection_toggle_requested = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("cameraPanel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Section title
        title = QLabel("Live Detection")
        title.setFont(QFont("-apple-system", 16, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #4a5568;")
        layout.addWidget(title)
        
        # Camera display widget
        self.camera_display = CameraDisplayWidget()
        self.camera_display.detection_toggle_requested.connect(self.detection_toggle_requested.emit)
        layout.addWidget(self.camera_display)
        
    def set_detection_state(self, detecting: bool):
        """Update detection state."""
        self.camera_display.set_detection_state(detecting)
        
    def update_frame(self, frame):
        """Update camera frame."""
        self.camera_display.update_frame(frame)
        
    def update_detection_data(self, detection_data):
        """Update detection overlay."""
        self.camera_display.update_detection_data(detection_data)


class AnalyticsPanel(QFrame):
    """Right panel containing session statistics."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("analyticsPanel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Section title
        title = QLabel("Today's Activity")
        title.setFont(QFont("-apple-system", 16, QFont.Weight.DemiBold))
        title.setStyleSheet("color: #4a5568;")
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        # Create stat cards
        self.create_stat_card(stats_layout, 0, 0, "0", "Detections")
        self.create_stat_card(stats_layout, 0, 1, "0m", "Session")
        self.create_stat_card(stats_layout, 1, 0, "0", "Mindful Stops")
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
    def create_stat_card(self, layout, row, col, value, label):
        """Create a statistics card widget."""
        card = QFrame()
        card.setFixedHeight(100)
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                padding: 24px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setFont(QFont("-apple-system", 32, QFont.Weight.Bold))
        value_label.setStyleSheet("color: white;")
        
        desc_label = QLabel(label)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setFont(QFont("-apple-system", 14))
        desc_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(desc_label)
        
        layout.addWidget(card, row, col)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.detection_worker = DetectionWorker()
        self.sound_manager = SoundManager()
        self.is_detecting = False
        
        # Initialize detection worker once at startup to avoid MediaPipe reinitialization
        self.detection_worker.initialize_detector()
        self.session_stats = {
            'detections': 0,
            'session_time': 0,
            'mindful_stops': 0
        }
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        self.setWindowTitle("Mindful Touch")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        self.header = HeaderWidget()
        main_layout.addWidget(self.header)
        
        # Content area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # Panels
        self.controls_panel = ControlsPanel()
        self.camera_panel = CameraPanel()
        self.analytics_panel = AnalyticsPanel()
        
        content_layout.addWidget(self.controls_panel)
        content_layout.addWidget(self.camera_panel, 1)  # Stretch factor 1
        content_layout.addWidget(self.analytics_panel)
        
        main_layout.addWidget(content_widget, 1)  # Stretch factor 1
        
        # Apply global stylesheet
        self.setStyleSheet(self.get_global_stylesheet())
        
    def setup_connections(self):
        """Connect signals between components."""
        # Controls panel connections
        self.controls_panel.region_toggled.connect(self.on_region_toggled)
        self.controls_panel.notification_settings_changed.connect(self.on_notification_settings_changed)
        self.controls_panel.test_sound_requested.connect(self.on_test_sound)
        
        # Camera panel connections
        self.camera_panel.detection_toggle_requested.connect(self.on_detection_toggle)
        
        # Detection worker connections
        self.detection_worker.detection_data.connect(self.on_detection_data)
        self.detection_worker.frame_ready.connect(self.on_frame_ready)
        self.detection_worker.error_occurred.connect(self.on_detection_error)
        
    def get_global_stylesheet(self):
        """Global application stylesheet."""
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
            
            #headerWidget {
                background: rgba(255, 255, 255, 0.95);
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            #controlsPanel, #cameraPanel, #analyticsPanel {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """
        
    def on_region_toggled(self, region: str, enabled: bool):
        """Handle region toggle changes."""
        print(f"Region {region} toggled: {enabled}")
        
        # Update detection worker with new enabled regions
        enabled_regions = self.controls_panel.get_enabled_regions()
        self.detection_worker.set_enabled_regions(enabled_regions)
        
    def on_notification_settings_changed(self, settings: dict):
        """Handle notification settings changes."""
        print(f"Notification settings changed: {settings}")
        
        # Update detection worker alert delay
        self.detection_worker.set_alert_delay(settings.get('delay', 3))
        
    def on_test_sound(self):
        """Handle test sound button click."""
        print("Test sound requested")
        
        # Get current sound type from controls panel
        settings = self.controls_panel.get_notification_settings()
        sound_type = settings.get('sound_type', 'Chime')
        
        # Play test sound
        success = self.sound_manager.test_sound(sound_type)
        if not success:
            print(f"Failed to play test sound: {sound_type}")
        
    def on_detection_toggle(self, start: bool):
        """Handle detection start/stop toggle."""
        print(f"Detection toggle requested: {start}")
        
        if start and not self.is_detecting:
            # Start detection
            self.is_detecting = True
            self.header.set_connected(True)
            self.camera_panel.set_detection_state(True)
            
            # Configure detection worker
            enabled_regions = self.controls_panel.get_enabled_regions()
            self.detection_worker.set_enabled_regions(enabled_regions)
            
            settings = self.controls_panel.get_notification_settings()
            self.detection_worker.set_alert_delay(settings.get('delay', 3))
            
            # Start detection worker
            self.detection_worker.start_detection()
            
        elif not start and self.is_detecting:
            # Stop detection
            self.is_detecting = False
            self.header.set_connected(False)
            self.camera_panel.set_detection_state(False)
            
            # Stop detection worker
            self.detection_worker.stop_detection()
            
    def on_detection_data(self, detection_data: dict):
        """Handle new detection data from worker thread."""
        # Update camera panel overlay
        self.camera_panel.update_detection_data(detection_data)
        
        # Handle alerts
        alert_regions = detection_data.get('alert_regions', [])
        if alert_regions:
            self.session_stats['detections'] += 1
            print(f"Alert! Regions: {alert_regions}")
            
            # Play sound alert if enabled
            settings = self.controls_panel.get_notification_settings()
            if settings.get('enabled') and settings.get('sound'):
                sound_type = settings.get('sound_type', 'Chime')
                self.sound_manager.play_sound(sound_type)
            
            # TODO: Update analytics panel display
        
    def on_frame_ready(self, frame):
        """Handle new camera frame from worker thread."""
        # Update camera display
        self.camera_panel.update_frame(frame)
        
    def on_detection_error(self, error_message: str):
        """Handle detection worker errors."""
        print(f"Detection error: {error_message}")
        
        # Stop detection on error
        if self.is_detecting:
            self.is_detecting = False
            self.header.set_connected(False)
            self.camera_panel.set_detection_state(False)
            
        # TODO: Show user-friendly error message
        
    def closeEvent(self, event):
        """Handle application close event."""
        # Stop detection worker before closing
        if self.is_detecting:
            self.detection_worker.stop_detection()
        
        # Wait for worker to finish
        if self.detection_worker.isRunning():
            self.detection_worker.wait(3000)
            
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Mindful Touch")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Mindful Touch")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())