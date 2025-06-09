import sys
import cv2
import numpy as np

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
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


# // NEW: A dedicated widget to display the camera feed.
class CameraFeedWidget(QWidget):
    """A widget to display the live video feed from the camera."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.camera_label = QLabel("Camera feed is hidden.", self)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("background-color: black; color: white; font-size: 16px;")
        layout.addWidget(self.camera_label)

    def update_frame(self, frame: np.ndarray):
        """Updates the label with a new frame from the detector."""
        if frame is None:
            return
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.camera_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.camera_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(e)


class MindfulTouchGUI(QMainWindow):
    """Main GUI window for Mindful Touch."""

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.detection_worker = None
        self.detection_thread = None
        self.session_active = False
        self.setup_ui()

    def setup_ui(self):
        """Setup the main user interface."""
        self.setWindowTitle("Mindful Touch")
        # // MODIFIED: Start with a compact size, allow expansion.
        self.setGeometry(100, 100, 450, 700)
        self.setMinimumSize(450, 700)

        # // MODIFIED: The central widget now uses a horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # // NEW: Create a left panel to hold all the original controls.
        self.left_panel = QWidget()
        left_panel_layout = QVBoxLayout(self.left_panel)
        left_panel_layout.setSpacing(15)
        left_panel_layout.setContentsMargins(15, 15, 15, 15)
        self.left_panel.setFixedWidth(450)  # Keep the control panel a consistent size

        # --- Add original widgets to the left panel ---
        self.create_header(left_panel_layout)
        self.status_widget = StatusWidget()
        left_panel_layout.addWidget(self.status_widget)
        self.settings_widget = SettingsWidget(self.config)
        self.settings_widget.settings_changed.connect(self.on_settings_changed)
        left_panel_layout.addWidget(self.settings_widget)
        self.create_privacy_section(left_panel_layout)
        self.create_control_buttons(left_panel_layout)
        main_layout.addWidget(self.left_panel)

        # // NEW: Create and add the camera feed widget to the main layout.
        self.camera_feed_widget = CameraFeedWidget()
        main_layout.addWidget(self.camera_feed_widget)
        self.camera_feed_widget.hide()  # Hide it by default.

        # // NEW: Connect the toggle signal from the settings widget.
        self.settings_widget.toggle_camera_feed_requested.connect(self.toggle_camera_feed)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready - Configure settings and start session")

    # // NEW: This method shows/hides the camera feed and resizes the window.
    def toggle_camera_feed(self, show: bool):
        if show:
            self.camera_feed_widget.show()
            # Use a QTimer to resize after the widget is shown to avoid glitches
            QTimer.singleShot(0, lambda: self.resize(self.minimumSizeHint()))
        else:
            self.camera_feed_widget.hide()
            # Resize back to the compact size of the left panel
            QTimer.singleShot(0, lambda: self.resize(self.left_panel.width(), self.height()))

    def start_session(self):
        """Start detection session."""
        try:
            self.settings_widget.update_config_from_ui()
            self.detection_worker = DetectionWorker(self.config)
            self.detection_thread = QThread()
            self.detection_worker.moveToThread(self.detection_thread)

            # Connect signals
            self.detection_worker.detection_occurred.connect(self.on_detection)
            self.detection_worker.error_occurred.connect(self.on_detection_error)
            self.detection_worker.status_update.connect(self.on_status_update)
            # // NEW: Connect the new frame_ready signal from the worker
            if hasattr(self.detection_worker, "frame_ready"):
                self.detection_worker.frame_ready.connect(self.on_frame_ready)

            self.detection_thread.started.connect(self.detection_worker.start_detection)
            self.detection_thread.start()

            self.session_active = True
            self.status_widget.start_session()
            self.start_button.setText("Stop Session")
            self.start_button.setStyleSheet(
                "background-color: #e74c3c; color: white; border: none; border-radius: 5px; padding: 8px;"
            )
            self.status_bar.showMessage("Session started - monitoring")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start session: {e}")

    # // NEW: A slot to receive the frame and pass it to the camera widget.
    def on_frame_ready(self, frame: np.ndarray):
        """Receives a frame from the worker and updates the camera feed if visible."""
        if self.camera_feed_widget.isVisible():
            self.camera_feed_widget.update_frame(frame)

    # ... (The rest of the file remains the same, only the setup_ui and start_session methods are modified as shown)
    def create_header(self, layout):
        """Create the header section."""
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        title = QLabel("Mindful Touch")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        header_layout.addWidget(title)
        subtitle = QLabel("Mindfulness tool for trichotillomania")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        header_layout.addWidget(subtitle)
        layout.addWidget(header_frame)

    def create_privacy_section(self, layout):
        """Create privacy section."""
        privacy_label = QLabel(
            "🔒 All processing happens locally on your device.\nNo camera data or personal information is sent anywhere."
        )
        privacy_label.setStyleSheet(
            "color: #2980b9; padding: 10px; background-color: #ecf0f1; border-radius: 5px; margin: 5px;"
        )
        privacy_label.setWordWrap(True)
        privacy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(privacy_label)

    def create_control_buttons(self, layout):
        """Create control buttons section."""
        button_frame = QFrame()
        button_layout = QVBoxLayout(button_frame)
        main_buttons = QHBoxLayout()
        self.start_button = QPushButton("Start Session")
        self.start_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.start_button.setMinimumHeight(40)
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; border: none; border-radius: 5px; padding: 8px; } QPushButton:hover { background-color: #229954; } QPushButton:pressed { background-color: #1e8449; }"
        )
        self.start_button.clicked.connect(self.toggle_session)
        main_buttons.addWidget(self.start_button)
        button_layout.addLayout(main_buttons)
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

    def stop_session(self):
        """Stop detection session."""
        self.session_active = False
        if self.detection_worker:
            self.detection_worker.stop_detection()
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.quit()
            self.detection_thread.wait(3000)
        self.status_widget.stop_session()
        self.start_button.setText("Start Session")
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; border: none; border-radius: 5px; padding: 8px; } QPushButton:hover { background-color: #229954; }"
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

    # Apply modern style
    app.setStyle("Fusion")

    window = MindfulTouchGUI()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main_gui())
