#!/usr/bin/env python3
"""
Mindful Touch - Modern Glass UI Implementation
Facial touch detection with beautiful, minimal interface
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QFont, QFontDatabase, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QMessageBox, QVBoxLayout, QWidget

from backend.detection import settings_store
from backend.detection.config import Config
from backend.detection.multi_region_detector import MultiRegionDetector
from ui.panels.camera_panel import CameraPanel
from ui.panels.detection_panel import DetectionPanel
from ui.styles.theme import Theme
from ui.widgets.status_badge import AppHeader, StatusBadge

ALERT_SOUND = "/System/Library/Sounds/Glass.aiff"


def resource_path(relative):
    """Resolve a bundled resource path (works in dev and inside PyInstaller)"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def load_fonts():
    """Register bundled Work Sans weights with Qt"""
    fonts_dir = Path(resource_path("assets/fonts"))
    if fonts_dir.exists():
        for font_file in sorted(fonts_dir.glob("*.ttf")):
            # addApplicationFontFromData: file-path loading is unreliable on macOS
            QFontDatabase.addApplicationFontFromData(font_file.read_bytes())


class CameraThread(QThread):
    """Thread for camera capture and detection"""

    frame_ready = pyqtSignal(np.ndarray)
    detection_data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False
        self.detector = None
        self.cap = None
        self.is_stopping = False

    def start_detection(self):
        """Start detection with proper state protection"""
        # Prevent starting if already running or stopping
        if self.running or self.is_stopping or self.isRunning():
            print("Detection already running or stopping, ignoring start request")
            return True  # Return True to not show error state in UI

        try:
            # Clean up any existing resources first
            self._cleanup_resources()

            # Create new detector and camera
            self.detector = MultiRegionDetector()
            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                print("Failed to open camera")
                self._cleanup_resources()
                return False

            # Set state and start thread
            self.running = True
            self.is_stopping = False
            self.start()
            return True

        except Exception as e:
            print(f"Error starting detection: {e}")
            self._cleanup_resources()
            return False

    def stop_detection(self):
        """Stop detection with proper state protection"""
        # Prevent double stopping
        if not self.running and not self.isRunning():
            print("Detection not running, ignoring stop request")
            return

        if self.is_stopping:
            print("Already stopping, ignoring stop request")
            return

        try:
            print("Stopping detection...")
            self.is_stopping = True
            self.running = False

            # Wait for thread to finish with timeout
            if self.isRunning():
                if not self.wait(3000):  # 3 second timeout
                    print("Warning: Thread did not stop gracefully, forcing termination")
                    self.terminate()
                    self.wait(1000)  # Wait 1 more second after terminate

            # Clean up resources
            self._cleanup_resources()
            self.is_stopping = False
            print("Detection stopped successfully")

        except Exception as e:
            print(f"Error stopping detection: {e}")
            self.is_stopping = False

    def _cleanup_resources(self):
        """Clean up camera and detector resources"""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None

            if self.detector:
                self.detector.cleanup()
                self.detector = None

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def run(self):
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            if self.detector:
                annotated_frame, detection_data = self.detector.process_frame(frame)
                self.frame_ready.emit(annotated_frame)
                self.detection_data.emit(detection_data)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.camera_thread = CameraThread()
        self.is_detecting = False
        self.show_feed = True
        self.current_flash_state = "none"
        self.is_transitioning = False  # Prevent rapid state changes

        # Session tracking
        self.session_start_time = None
        self.total_detections = 0
        self.mindful_stops = 0
        self.last_alert_state = False

        # Timer for session updates
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)

        # Load persisted settings before building the UI so toggles initialize correctly
        self.settings = settings_store.load()
        Config.ACTIVE_REGIONS = [r for r in self.settings["active_regions"] if r in Config.AVAILABLE_REGIONS]
        Config.update_contact_duration(self.settings["alert_delay"])

        self.setup_ui()
        self.setup_menu()
        self.connect_signals()

        self.detection_panel.set_contact_duration(self.settings["alert_delay"])

    def setup_ui(self):
        self.setWindowTitle("Mindful Touch")
        self.setMinimumSize(Theme.WINDOW_MIN_WIDTH, Theme.WINDOW_MIN_HEIGHT)

        # Glass background lives on the central widget (targeted by objectName so
        # flash styles never cascade into child widgets)
        central_widget = QWidget()
        central_widget.setObjectName("central")
        central_widget.setStyleSheet(self._central_style())
        self.setCentralWidget(central_widget)

        # Main layout: full-width header bar with hairline, then padded content
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header bar (border spans the full window width, like the design)
        header_bar = QWidget()
        header_bar.setObjectName("headerBar")
        header_bar.setStyleSheet(f"""
            QWidget#headerBar {{
                background: transparent;
                border-bottom: 1px solid {Theme.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(32, 22, 32, 18)
        header_layout.setSpacing(Theme.ITEM_SPACING)

        # App title
        self.app_header = AppHeader()
        header_layout.addWidget(self.app_header)

        header_layout.addStretch()

        # Status badge
        self.status_badge = StatusBadge()
        header_layout.addWidget(self.status_badge)

        main_layout.addWidget(header_bar)

        # Content area - 2 column layout (camera 1.4fr / controls 1fr)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(32, Theme.CARD_MARGIN, 32, 32)
        content_layout.setSpacing(Theme.CARD_MARGIN)

        # Left panel - Camera and stats
        self.camera_panel = CameraPanel()
        content_layout.addWidget(self.camera_panel, stretch=7)

        # Right panel - Detection controls
        self.detection_panel = DetectionPanel()
        content_layout.addWidget(self.detection_panel, stretch=5)

        main_layout.addLayout(content_layout)

    def setup_menu(self):
        menubar = self.menuBar()

        app_menu = menubar.addMenu("Mindful Touch")

        about_action = QAction("About Mindful Touch", self)
        about_action.triggered.connect(self._show_about)
        app_menu.addAction(about_action)

        app_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        app_menu.addAction(quit_action)

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Mindful Touch",
            "Mindful Touch v1.0\n\n"
            "A gentle awareness tool that helps you notice\n"
            "unconscious face-touching habits.\n\n"
            "All processing happens locally on your device.\n"
            "No data is collected or transmitted.",
        )

    def connect_signals(self):
        # Camera thread signals
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread.detection_data.connect(self.update_detection)

        # Panel signals
        self.detection_panel.region_toggled.connect(self.toggle_region)
        self.detection_panel.contact_duration_changed.connect(self.update_contact_duration)
        self.detection_panel.detection_button_clicked.connect(self._on_detection_button)

        self.camera_panel.toggle_privacy.connect(self.toggle_privacy)

    def _on_detection_button(self):
        """Start/pause toggle from the detection panel"""
        if self.is_detecting:
            self.stop_detection()
        else:
            self.start_detection()

    def update_camera(self, frame):
        """Update camera display with error handling"""
        try:
            # Only update camera if detection is running
            if self.is_detecting and frame is not None:
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()

                pixmap = QPixmap.fromImage(q_image)
                # Scale to fit the actual camera label size
                label_size = self.camera_panel.camera_label.size()
                scaled_pixmap = pixmap.scaled(label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.camera_panel.update_camera_frame(scaled_pixmap)
        except Exception as e:
            print(f"Error updating camera display: {e}")
            # Don't crash the app on camera display errors

    def update_detection(self, data):
        """Update detection data with error handling"""
        try:
            if not data or not self.is_detecting:
                return

            # Update visual flash state
            regions_with_contact = data.get("regions_with_contact", [])
            region_details = data.get("region_details", {})
            alerts_active = data.get("alerts_active", [])
            mindful_stops_detected = data.get("mindful_stops_detected", [])

            # Play sound when alerts are triggered (with proper cooldown from backend)
            if alerts_active:
                self._play_alert_sound()

            # Check if any regions have active alerts
            active_alert_regions = [region for region, details in region_details.items() if details.get("alert_active", False)]
            current_alert_state = len(active_alert_regions) > 0

            # Track session statistics
            if current_alert_state and not self.last_alert_state:
                # New alert triggered
                self.total_detections += 1
            elif self.last_alert_state and not current_alert_state:
                # Alert ended (also count as mindful stop)
                self.mindful_stops += 1

            # Count quick hand removals as mindful stops
            if mindful_stops_detected:
                self.mindful_stops += len(mindful_stops_detected)
                self.camera_panel.show_mindful_stop_flash()
                print(f"Mindful stop detected in regions: {mindful_stops_detected}")

            self.last_alert_state = current_alert_state

            # Update status badge
            if active_alert_regions:
                self.status_badge.set_status("alert")
                self.set_flash_state("red")
            elif regions_with_contact:
                self.status_badge.set_status("detecting")
                self.set_flash_state("orange")
            else:
                if self.is_detecting:
                    self.status_badge.set_status("detecting")
                else:
                    self.status_badge.set_status("ready")
                self.set_flash_state("none")

            # Update activity stats
            self.camera_panel.update_stats(self.total_detections, self._get_session_seconds(), self.mindful_stops)

        except Exception as e:
            print(f"Error updating detection data: {e}")
            # Don't crash the app on detection update errors

    def start_detection(self):
        """Start detection process with UI state management"""
        # Prevent rapid clicking
        if self.is_transitioning or self.is_detecting:
            print("Start detection ignored - already detecting or transitioning")
            return

        try:
            print("Starting detection...")
            self.is_transitioning = True

            # Disable buttons during transition
            self._set_buttons_enabled(False)
            self.status_badge.set_status("detecting")

            # Attempt to start camera thread
            if self.camera_thread.start_detection():
                # Success - update state
                self.is_detecting = True
                self.session_start_time = time.time()
                self.total_detections = 0
                self.mindful_stops = 0
                self.last_alert_state = False

                # Start session timer
                self.session_timer.start(1000)  # Update every second

                # Update UI
                self.camera_panel.set_detection_state(True)
                self.detection_panel.set_detection_state(True)
                print("Detection started successfully")

            else:
                # Failed to start - revert state
                print("Failed to start detection")
                self.status_badge.set_status("ready")

        except Exception as e:
            print(f"Error in start_detection: {e}")
            self.status_badge.set_status("ready")

        finally:
            self.is_transitioning = False
            self._set_buttons_enabled(True)

    def stop_detection(self):
        """Stop detection process with UI state management"""
        # Prevent rapid clicking
        if self.is_transitioning or not self.is_detecting:
            print("Stop detection ignored - not detecting or transitioning")
            return

        try:
            print("Stopping detection...")
            self.is_transitioning = True

            # Disable buttons during transition
            self._set_buttons_enabled(False)

            # Stop camera thread
            self.camera_thread.stop_detection()

            # Update state
            self.is_detecting = False
            self.session_start_time = None

            # Stop session timer
            self.session_timer.stop()

            # Update UI
            self.camera_panel.set_detection_state(False)
            self.detection_panel.set_detection_state(False)
            self.status_badge.set_status("ready")
            self.show_feed = True
            self.set_flash_state("none")
            print("Detection stopped successfully")

        except Exception as e:
            print(f"Error in stop_detection: {e}")

        finally:
            self.is_transitioning = False
            self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled):
        """Enable/disable detection buttons during state transitions"""
        try:
            self.detection_panel.set_button_enabled(enabled)
        except Exception as e:
            print(f"Error setting button states: {e}")

    def toggle_privacy(self):
        """Toggle camera feed visibility without stopping detection"""
        self.show_feed = not self.show_feed
        self.camera_panel.set_privacy_state(self.show_feed)

    def _central_style(self, tint=None, border_color=None):
        """Build the central widget stylesheet, optionally tinted for alerts"""
        if tint and border_color:
            background = tint
            border = f"border-top: 3px solid {border_color};"
        else:
            background = Theme.CANVAS
            border = ""
        return f"""
            QWidget#central {{
                background: {background};
                {border}
            }}
        """

    def set_flash_state(self, state):
        """Tint the window background and top border to signal contact/alert"""
        if state == self.current_flash_state:
            return

        self.current_flash_state = state

        if state == "red":
            # Touch noticed — warm clay tint
            style = self._central_style(Theme.SOFT_CLAY, Theme.CLAY)
        elif state == "orange":
            # Hand near a region — gentle blue tint
            style = self._central_style(Theme.SOFT_BLUE, Theme.PRIMARY)
        else:
            style = self._central_style()
        self.centralWidget().setStyleSheet(style)

    def toggle_region(self, region: str, enabled: bool):
        """Handle region toggle from settings panel"""
        # Update Config directly so toggles work before detection starts too;
        # the detector reads Config.ACTIVE_REGIONS live on every frame
        if enabled and region not in Config.ACTIVE_REGIONS:
            Config.ACTIVE_REGIONS.append(region)
        elif not enabled and region in Config.ACTIVE_REGIONS:
            Config.ACTIVE_REGIONS.remove(region)

        self.settings["active_regions"] = list(Config.ACTIVE_REGIONS)
        settings_store.save(self.settings)

    def update_contact_duration(self, duration: float):
        """Handle contact duration change from settings panel"""
        Config.update_contact_duration(duration)
        self.settings["alert_delay"] = duration
        settings_store.save(self.settings)

    def _update_session_timer(self):
        """Update session timer display"""
        if self.is_detecting and self.session_start_time:
            self.camera_panel.update_stats(self.total_detections, self._get_session_seconds(), self.mindful_stops)

    def _get_session_seconds(self):
        """Get current session duration in seconds"""
        if self.session_start_time:
            return int(time.time() - self.session_start_time)
        return 0

    def _play_alert_sound(self):
        """Play alert sound - cooldown already handled by backend"""
        try:
            subprocess.Popen(["afplay", ALERT_SOUND, "-t", "0.35"])
        except Exception as e:
            print(f"Could not play sound: {e}")

    def closeEvent(self, event):
        """Ensure proper cleanup when app is closed"""
        try:
            print("Application closing, cleaning up...")

            # Stop detection if running
            if self.is_detecting:
                print("Stopping detection before exit...")
                self.camera_thread.stop_detection()

            # Stop any timers
            if self.session_timer.isActive():
                self.session_timer.stop()

            # Force cleanup of camera thread
            if self.camera_thread.isRunning():
                print("Forcing camera thread cleanup...")
                self.camera_thread.terminate()
                self.camera_thread.wait(2000)  # Wait up to 2 seconds

            print("Application cleanup completed")

        except Exception as e:
            print(f"Error during application cleanup: {e}")

        finally:
            event.accept()


def main():
    app = QApplication(sys.argv)
    load_fonts()
    app.setFont(QFont(Theme.FONT_BODY, 13))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
