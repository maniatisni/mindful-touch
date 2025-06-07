"""Qt-based GUI for Mindful Touch application."""

import sys
import threading
import time
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QSlider,
    QCheckBox,
    QLineEdit,
    QGroupBox,
    QTextEdit,
    QProgressBar,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QFont, QPixmap, QIcon

from ..config import ConfigManager
from ..detector import HandFaceDetector, DetectionEvent
from ..notifier import NotificationManager


class DetectionWorker(QObject):
    """Worker thread for hand detection."""

    detection_occurred = Signal()
    error_occurred = Signal(str)
    status_update = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = ConfigManager().load_config()
        self.detector = None
        self.running = False
        self.notifier = NotificationManager(self.config.notifications)

    def start_detection(self):
        """Start the detection process."""
        try:
            self.detector = HandFaceDetector(detection_config=self.config.detection, camera_config=self.config.camera)
            self.detector.initialize_camera()
            self.running = True
            self.status_update.emit("Detection started")

            while self.running:
                self.detector.detection_config = self.config.detection
                self.notifier.config = self.config.notifications

                result = self.detector.capture_and_detect()
                if not result:
                    time.sleep(0.001)
                    continue

                # Handle detection events
                if result.event == DetectionEvent.HAND_NEAR_FACE:
                    if self.notifier.show_mindful_moment():
                        print(f"🌸 Mindful moment (distance: {result.min_hand_face_distance_cm:.1f}cm)")
                    else:
                        cooldown: float = self.notifier.get_cooldown_remaining()
                        if cooldown > 0:
                            print(f"🔇 Cooldown: {cooldown:.1f}s")
                elif result.event == DetectionEvent.EYEBROW_PINCH:
                    self.notifier._show_notification(
                        title="Eyebrow Pinch Detected", message="Stop touching your eyebrows!❤️"
                    )
                    print(f"⚠️ Eyebrow pinching detected! (distance: {result.min_hand_face_distance_cm:.1f}cm)")
                elif result.event == DetectionEvent.SCALP_PINCH:
                    self.notifier._show_notification(
                        title="Scalp/Temple Pinch Detected", message="Stop pinching your scalp/temple!❤️"
                    )
                    print(f"⚠️ Scalp/temple pinching detected! (distance: {result.min_hand_face_distance_cm:.1f}cm)")

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if self.detector:
                self.detector.cleanup()

    def stop_detection(self):
        """Stop the detection process."""
        self.running = False
        if self.detector:
            self.detector.cleanup()
        self.status_update.emit("Detection stopped")


class MindfulTouchGUI(QMainWindow):
    """Main GUI window for Mindful Touch."""

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config = ConfigManager().load_config()

        # Initialize components
        self.notification_manager = NotificationManager(self.config.notifications)
        self.detection_worker = None
        self.detection_thread = None
        self.session_active = False
        self.detection_count = 0
        self.session_start_time = None

        # Setup UI
        self.setup_ui()
        self.load_config_to_ui()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_session_time)

    def setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("Mindful Touch - Trichotillomania Detection")
        self.setGeometry(100, 100, 600, 700)
        self.setMinimumSize(500, 600)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)

        # Header
        self.create_header(layout)

        # Status section
        self.create_status_section(layout)

        # Detection settings
        self.create_detection_settings(layout)

        # Notification settings
        self.create_notification_settings(layout)

        # Privacy section
        self.create_privacy_section(layout)

        # Control buttons
        self.create_control_buttons(layout)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Configure settings and start session")

    def create_header(self, layout):
        """Create the header section."""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)

        # Title
        title = QLabel("Mindful Touch")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        header_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Mindfulness tool for trichotillomania")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

    def create_status_section(self, layout):
        """Create the session status section."""
        status_group = QGroupBox("Session Status")
        status_layout = QVBoxLayout(status_group)

        # Status indicator and text
        status_row = QHBoxLayout()
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.status_indicator.setStyleSheet("color: #e74c3c;")
        status_row.addWidget(self.status_indicator)

        self.status_text = QLabel("Session Inactive")
        self.status_text.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_row.addWidget(self.status_text)
        status_row.addStretch()
        status_layout.addLayout(status_row)

        # Session statistics
        stats_layout = QHBoxLayout()

        self.detection_count_label = QLabel("Detections: 0")
        stats_layout.addWidget(self.detection_count_label)

        self.session_time_label = QLabel("Session time: 00:00")
        stats_layout.addWidget(self.session_time_label)
        stats_layout.addStretch()

        status_layout.addLayout(stats_layout)

        # Progress bar for calibration/startup
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)

    def create_detection_settings(self, layout):
        """Create detection settings section."""
        detection_group = QGroupBox("Detection Settings")
        detection_layout = QVBoxLayout(detection_group)

        # Sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 100)  # 0.1 to 1.0
        self.sensitivity_slider.setValue(50)
        self.sensitivity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sensitivity_slider.setTickInterval(10)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        self.sensitivity_value = QLabel("0.5")
        self.sensitivity_value.setMinimumWidth(30)
        sensitivity_layout.addWidget(self.sensitivity_value)
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity_label)
        detection_layout.addLayout(sensitivity_layout)

        # Hand-face threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Hand-Face Distance (cm):"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(2, 50)
        self.threshold_slider.setValue(15)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(5)
        threshold_layout.addWidget(self.threshold_slider)
        self.threshold_value = QLabel("15")
        self.threshold_value.setMinimumWidth(30)
        threshold_layout.addWidget(self.threshold_value)
        self.threshold_slider.valueChanged.connect(self.update_threshold_label)
        detection_layout.addLayout(threshold_layout)

        # Confidence threshold
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Confidence Threshold:"))
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(10, 100)  # 0.1 to 1.0
        self.confidence_slider.setValue(70)
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        confidence_layout.addWidget(self.confidence_slider)
        self.confidence_value = QLabel("0.7")
        self.confidence_value.setMinimumWidth(30)
        confidence_layout.addWidget(self.confidence_value)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        detection_layout.addLayout(confidence_layout)

        layout.addWidget(detection_group)

    def create_notification_settings(self, layout):
        """Create notification settings section."""
        notification_group = QGroupBox("Notification Settings")
        notification_layout = QVBoxLayout(notification_group)

        # Enable notifications
        self.notifications_enabled = QCheckBox("Enable Notifications")
        self.notifications_enabled.setChecked(True)
        notification_layout.addWidget(self.notifications_enabled)

        # Notification message
        message_layout = QHBoxLayout()
        message_layout.addWidget(QLabel("Message:"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter notification message...")
        message_layout.addWidget(self.message_input)
        notification_layout.addLayout(message_layout)

        # Cooldown period
        cooldown_layout = QHBoxLayout()
        cooldown_layout.addWidget(QLabel("Cooldown (seconds):"))
        self.cooldown_slider = QSlider(Qt.Orientation.Horizontal)
        self.cooldown_slider.setRange(5, 60)
        self.cooldown_slider.setValue(10)
        self.cooldown_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.cooldown_slider.setTickInterval(5)
        cooldown_layout.addWidget(self.cooldown_slider)
        self.cooldown_value = QLabel("10")
        self.cooldown_value.setMinimumWidth(30)
        cooldown_layout.addWidget(self.cooldown_value)
        self.cooldown_slider.valueChanged.connect(self.update_cooldown_label)
        notification_layout.addLayout(cooldown_layout)

        layout.addWidget(notification_group)

    def create_privacy_section(self, layout):
        """Create privacy and data section."""
        privacy_group = QGroupBox("Privacy & Data")
        privacy_layout = QVBoxLayout(privacy_group)

        # Privacy message
        privacy_label = QLabel(
            "🔒 All processing happens locally on your device.\n"
            "No camera data or personal information is sent anywhere.\n"
            "Your privacy is completely protected."
        )
        privacy_label.setStyleSheet("color: #2980b9; padding: 10px; background-color: #ecf0f1; border-radius: 5px;")
        privacy_label.setWordWrap(True)
        privacy_layout.addWidget(privacy_label)

        # Data logging option
        self.log_detections = QCheckBox("Log detection events locally (for your own tracking)")
        self.log_detections.setChecked(True)
        privacy_layout.addWidget(self.log_detections)

        layout.addWidget(privacy_group)

    def create_control_buttons(self, layout):
        """Create control buttons section."""
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)

        # Main action buttons
        main_buttons = QHBoxLayout()

        self.start_button = QPushButton("Start Session")
        self.start_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """
        )
        self.start_button.clicked.connect(self.toggle_session)
        main_buttons.addWidget(self.start_button)

        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setMinimumHeight(40)
        self.calibrate_button.clicked.connect(self.run_calibration)
        main_buttons.addWidget(self.calibrate_button)

        button_layout.addLayout(main_buttons)

        # Secondary buttons
        secondary_buttons = QHBoxLayout()

        test_notification_btn = QPushButton("Test Notification")
        test_notification_btn.clicked.connect(self.test_notification)
        secondary_buttons.addWidget(test_notification_btn)

        save_settings_btn = QPushButton("Save Settings")
        save_settings_btn.clicked.connect(self.save_settings)
        secondary_buttons.addWidget(save_settings_btn)

        button_layout.addLayout(secondary_buttons)

        layout.addWidget(button_frame)

    def load_config_to_ui(self):
        """Load configuration values into UI elements."""
        # Detection settings
        self.sensitivity_slider.setValue(int(self.config.detection.sensitivity * 100))
        self.threshold_slider.setValue(int(self.config.detection.hand_face_threshold_cm))
        self.confidence_slider.setValue(int(self.config.detection.confidence_threshold * 100))

        # Notification settings
        self.notifications_enabled.setChecked(self.config.notifications.enabled)
        self.message_input.setText(self.config.notifications.message)
        self.cooldown_slider.setValue(self.config.notifications.cooldown_seconds)

        # Update labels
        self.update_sensitivity_label(self.sensitivity_slider.value())
        self.update_threshold_label(self.threshold_slider.value())
        self.update_confidence_label(self.confidence_slider.value())
        self.update_cooldown_label(self.cooldown_slider.value())

    def update_sensitivity_label(self, value):
        """Update sensitivity label."""
        self.sensitivity_value.setText(f"{value/100:.1f}")

    def update_threshold_label(self, value):
        """Update threshold label."""
        self.threshold_value.setText(f"{value}")

    def update_confidence_label(self, value):
        """Update confidence label."""
        self.confidence_value.setText(f"{value/100:.1f}")

    def update_cooldown_label(self, value):
        """Update cooldown label."""
        self.cooldown_value.setText(f"{value}")

    def toggle_session(self):
        """Start or stop detection session."""
        if self.session_active:
            self.stop_session()
        else:
            self.start_session()

    def start_session(self):
        """Start detection session."""
        try:
            # Update config from UI
            self.update_config_from_ui()

            # Initialize detection worker
            self.detection_worker = DetectionWorker(self.config)
            self.detection_thread = QThread()
            self.detection_worker.moveToThread(self.detection_thread)

            # Connect signals
            self.detection_worker.detection_occurred.connect(self.on_detection)
            self.detection_worker.error_occurred.connect(self.on_detection_error)
            self.detection_worker.status_update.connect(self.on_status_update)
            self.detection_thread.started.connect(self.detection_worker.start_detection)

            # Start thread
            self.detection_thread.start()

            # Update UI
            self.session_active = True
            self.detection_count = 0
            self.session_start_time = time.time()

            self.start_button.setText("Stop Session")
            self.start_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """
            )

            self.status_indicator.setStyleSheet("color: #27ae60;")
            self.status_text.setText("Session Active - Monitoring")
            self.update_timer.start(1000)  # Update every second

            self.status_bar.showMessage("Session started - monitoring for hand-face proximity")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start session: {e}")

    def stop_session(self):
        """Stop detection session."""
        self.session_active = False

        if self.detection_worker:
            self.detection_worker.stop_detection()

        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.quit()
            self.detection_thread.wait(3000)  # Wait up to 3 seconds

        # Update UI
        self.start_button.setText("Start Session")
        self.start_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """
        )

        self.status_indicator.setStyleSheet("color: #e74c3c;")
        self.status_text.setText("Session Inactive")
        self.update_timer.stop()

        self.status_bar.showMessage("Session stopped")

    def on_detection(self):
        """Handle detection event."""
        self.detection_count += 1
        self.detection_count_label.setText(f"Detections: {self.detection_count}")

        # Send notification if enabled
        if self.notifications_enabled.isChecked():
            self.notification_manager.send_notification(
                title=self.config.notification.title,
                message=self.message_input.text() or self.config.notification.message,
            )

        self.status_bar.showMessage(f"Detection #{self.detection_count} - Take a mindful moment", 3000)

    def on_detection_error(self, error_msg):
        """Handle detection error."""
        self.status_bar.showMessage(f"Detection error: {error_msg}", 5000)
        QMessageBox.warning(self, "Detection Error", f"An error occurred during detection:\n{error_msg}")

    def on_status_update(self, message):
        """Handle status updates from detection worker."""
        self.status_bar.showMessage(message, 2000)

    def update_session_time(self):
        """Update session time display."""
        if self.session_active and self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            minutes, seconds = divmod(elapsed, 60)
            self.session_time_label.setText(f"Session time: {minutes:02d}:{seconds:02d}")

    def run_calibration(self):
        """Run calibration process."""
        self.calibrate_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_bar.showMessage("Running calibration...")

        # Run calibration in separate thread
        def calibration_thread():
            try:
                from ..commands.calibrate import run_calibration

                result = run_calibration(duration=10)

                if result and "suggested_threshold" in result:
                    # Update UI in main thread
                    self.threshold_slider.setValue(int(result["suggested_threshold"]))
                    self.status_bar.showMessage(
                        f"Calibration complete. Suggested threshold: {result['suggested_threshold']:.1f}cm", 5000
                    )
                else:
                    self.status_bar.showMessage("Calibration completed", 3000)

            except Exception as e:
                QMessageBox.warning(self, "Calibration Error", f"Calibration failed: {e}")
            finally:
                # Reset UI in main thread
                self.calibrate_button.setEnabled(True)
                self.progress_bar.setVisible(False)

        threading.Thread(target=calibration_thread, daemon=True).start()

    def test_notification(self):
        """Test notification system."""
        try:
            message = self.message_input.text() or "Test notification from Mindful Touch!"
            self.notification_manager.send_notification(title="Mindful Touch Test", message=message)
            self.status_bar.showMessage("Test notification sent", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Notification Error", f"Failed to send notification: {e}")

    def update_config_from_ui(self):
        """Update configuration from UI values."""
        self.config.detection.sensitivity = self.sensitivity_slider.value() / 100
        self.config.detection.hand_face_threshold_cm = self.threshold_slider.value()
        self.config.detection.confidence_threshold = self.confidence_slider.value() / 100
        self.config.notifications.enabled = self.notifications_enabled.isChecked()
        self.config.notifications.message = self.message_input.text()
        self.config.notifications.cooldown_seconds = self.cooldown_slider.value()

    def save_settings(self):
        """Save current settings to configuration file."""
        try:
            self.update_config_from_ui()
            ConfigManager.save_config(self.config)
            self.status_bar.showMessage("Settings saved successfully", 3000)
            QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")

    def closeEvent(self, event):
        """Handle window close event."""
        if self.session_active:
            reply = QMessageBox.question(
                self,
                "Session Active",
                "A detection session is currently active. Do you want to stop it and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.stop_session()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main_gui():
    """Launch the Qt GUI application."""
    app = QApplication(sys.argv)
    app.setApplicationName("Mindful Touch")
    app.setOrganizationName("Mindful Touch Project")

    # Apply modern style
    app.setStyle("Fusion")

    window = MindfulTouchGUI()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main_gui())
