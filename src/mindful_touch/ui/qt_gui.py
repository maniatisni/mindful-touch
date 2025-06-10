"""Simplified Qt-based GUI for Mindful Touch application."""

import os
import sys

from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import ConfigManager
from ..notifier import NotificationManager
from .detection_worker import DetectionWorker
from .settings_widget import SettingsWidget
from .status_widget import StatusWidget


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
        self.setMinimumSize(750, 850)

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
        """Create the header section with a modern look and logo image."""

        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)

        logo_path = os.path.join(os.getcwd(), "logo.png")
        logo_label = QLabel()
        logo_label.setFixedSize(200, 200)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            # Crop to circle
            size = min(pixmap.width(), pixmap.height(), 200)
            cropped = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            mask = QPixmap(size, size)
            mask.fill(Qt.transparent)
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, cropped)
            painter.end()
            logo_label.setPixmap(mask)
            logo_label.setStyleSheet("margin-top: 18px; margin-bottom: 8px;")
            header_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            # Fallback to emoji if image not found
            logo_label.setText("🌸")
            logo_label.setStyleSheet(
                """
                QLabel {
                    background: qradialgradient(cx:0.5, cy:0.5, radius:0.8, fx:0.5, fy:0.5, stop:0 #f8fafc, stop:1 #e0c3fc);
                    border-radius: 70px;
                    font-size: 80px;
                    margin-top: 18px;
                    margin-bottom: 8px;
                    box-shadow: 0 2px 8px rgba(44,62,80,0.08);
                }
                """
            )
            header_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_frame)

    def create_privacy_section(self, layout):
        """Create privacy section."""
        privacy_label = QLabel(
            "🔒 All processing happens locally on your device.\n"
            "No camera data or personal information is sent anywhere."
        )
        privacy_label.setStyleSheet(
            "color: white; padding: 10px; background-color: #6c757d; " "border-radius: 5px; margin: 5px;"
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
    icon_path = os.path.join(os.getcwd(), "logo.icns")
    app.setWindowIcon(QIcon(icon_path))
    # Apply modern style
    app.setStyle("Fusion")

    window = MindfulTouchGUI()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main_gui())
