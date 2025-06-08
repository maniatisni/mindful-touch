"""Simplified Qt-based GUI for Mindful Touch application."""

import sys
import threading
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QLabel,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QFont

from ..config import ConfigManager
from ..detector import HandFaceDetector
from ..notifier import NotificationManager
from .detection_worker import DetectionWorker
from .status_widget import StatusWidget
from .settings_widget import SettingsWidget


class MindfulTouchGUI(QMainWindow):
    """Main GUI window for Mindful Touch."""

    def __init__(self):
        super().__init__()

        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()

        # Initialize components
        self.detection_worker = None
        self.detection_thread = None
        self.session_active = False

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("Mindful Touch - Trichotillomania Detection")
        self.setGeometry(100, 100, 500, 600)
        self.setMinimumSize(650, 800)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)

        # Header
        self.create_header(layout)

        # Status widget
        self.status_widget = StatusWidget()
        layout.addWidget(self.status_widget)

        # Settings widget
        self.settings_widget = SettingsWidget(self.config)
        self.settings_widget.settings_changed.connect(self.on_settings_changed)
        layout.addWidget(self.settings_widget)

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

    def create_privacy_section(self, layout):
        """Create privacy section."""
        privacy_label = QLabel(
            "🔒 All processing happens locally on your device.\n"
            "No camera data or personal information is sent anywhere."
        )
        privacy_label.setStyleSheet(
            "color: #2980b9; padding: 10px; background-color: #ecf0f1; " "border-radius: 5px; margin: 5px;"
        )
        privacy_label.setWordWrap(True)
        privacy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(privacy_label)

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
            self.settings_widget.update_config_from_ui()

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
            self.status_widget.start_session()

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
        self.status_widget.stop_session()

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

        self.status_bar.showMessage("Session stopped")

    def on_detection(self, distance: float):
        """Handle detection event."""
        self.status_widget.add_detection(distance)
        self.status_bar.showMessage(f"Detection - distance: {distance:.1f}cm - Take a mindful moment", 3000)

    def on_detection_error(self, error_msg: str):
        """Handle detection error."""
        self.status_bar.showMessage(f"Detection error: {error_msg}", 5000)
        QMessageBox.warning(self, "Detection Error", f"An error occurred during detection:\n{error_msg}")

    def on_status_update(self, message: str):
        """Handle status updates from detection worker."""
        self.status_bar.showMessage(message, 2000)

    def on_settings_changed(self):
        """Handle settings changes."""
        # No need to save automatically, user can click Save Settings
        pass

    def run_calibration(self):
        """Run calibration process."""
        self.calibrate_button.setEnabled(False)
        self.status_widget.show_progress("Running calibration...")

        def calibration_thread():
            try:
                detector = HandFaceDetector(self.config.detection, self.config.camera)
                result = detector.calibrate(duration_seconds=10)

                if result and "suggested_threshold" in result and "error" not in result:
                    # Update UI in main thread
                    QTimer.singleShot(0, lambda: self.apply_calibration_result(result))
                else:
                    error = result.get("error", "Unknown calibration error")
                    QTimer.singleShot(0, lambda: self.show_calibration_error(error))

            except Exception as e:
                QTimer.singleShot(0, lambda: self.show_calibration_error(str(e)))
            finally:
                # Reset UI in main thread
                QTimer.singleShot(0, self.reset_calibration_ui)

        threading.Thread(target=calibration_thread, daemon=True).start()

    def apply_calibration_result(self, result):
        """Apply calibration result to UI."""
        suggested = result["suggested_threshold"]
        self.settings_widget.threshold_slider.setValue(int(suggested))
        self.status_bar.showMessage(f"Calibration complete. Suggested threshold: {suggested:.1f}cm", 5000)

    def show_calibration_error(self, error):
        """Show calibration error."""
        QMessageBox.warning(self, "Calibration Error", f"Calibration failed: {error}")

    def reset_calibration_ui(self):
        """Reset calibration UI elements."""
        self.calibrate_button.setEnabled(True)
        self.status_widget.hide_progress()

    def test_notification(self):
        """Test notification system."""
        try:
            notifier = NotificationManager(self.config.notifications)
            if notifier.test_notification():
                self.status_bar.showMessage("Test notification sent", 3000)
            else:
                self.status_bar.showMessage("Test notification failed", 3000)
        except Exception as e:
            QMessageBox.warning(self, "Notification Error", f"Failed to send notification: {e}")

    def save_settings(self):
        """Save current settings to configuration file."""
        try:
            self.settings_widget.update_config_from_ui()
            self.config_manager.save_config(self.config)
            self.status_bar.showMessage("Settings saved successfully", 3000)
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
