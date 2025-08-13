#!/usr/bin/env python3
"""
Mindful Touch - Modern Glass UI Implementation
Facial touch detection with beautiful, minimal interface
"""

import subprocess
import sys
import time

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from backend.detection.config import Config
from backend.detection.multi_region_detector import MultiRegionDetector
from ui.panels.camera_panel import CameraPanel
from ui.panels.detection_panel import DetectionPanel
from ui.styles.theme import Theme
from ui.widgets.status_badge import AppHeader, StatusBadge


class CameraThread(QThread):
    """Thread for camera capture and detection"""

    frame_ready = pyqtSignal(np.ndarray)
    detection_data = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.running = False
        self.detector = None
        self.cap = None

    def start_detection(self):
        self.detector = MultiRegionDetector()
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            return False

        self.running = True
        self.start()
        return True

    def stop_detection(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.detector:
            self.detector.cleanup()
        self.wait()

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

        # Session tracking
        self.session_start_time = None
        self.total_detections = 0
        self.mindful_stops = 0
        self.last_alert_state = False

        # Timer for session updates
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session_timer)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setWindowTitle("Mindful Touch")
        self.setMinimumSize(Theme.WINDOW_MIN_WIDTH, Theme.WINDOW_MIN_HEIGHT)

        # Set glass background
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {Theme.BACKGROUND};
            }}
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with margins
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(Theme.CARD_MARGIN, Theme.CARD_MARGIN, Theme.CARD_MARGIN, Theme.CARD_MARGIN)
        main_layout.setSpacing(Theme.CARD_MARGIN)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(Theme.ITEM_SPACING)

        # App title
        self.app_header = AppHeader()
        header_layout.addWidget(self.app_header)

        header_layout.addStretch()

        # Status badge
        self.status_badge = StatusBadge()
        header_layout.addWidget(self.status_badge)

        main_layout.addLayout(header_layout)

        # Content area - 2 column layout
        content_layout = QHBoxLayout()
        content_layout.setSpacing(Theme.CARD_MARGIN)

        # Left panel - Detection controls
        self.detection_panel = DetectionPanel()
        self.detection_panel.setFixedWidth(400)
        content_layout.addWidget(self.detection_panel)

        # Right panel - Camera and stats
        self.camera_panel = CameraPanel()
        content_layout.addWidget(self.camera_panel)

        main_layout.addLayout(content_layout)

    def connect_signals(self):
        # Camera thread signals
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread.detection_data.connect(self.update_detection)

        # Panel signals
        self.detection_panel.region_toggled.connect(self.toggle_region)
        self.detection_panel.contact_duration_changed.connect(self.update_contact_duration)

        self.camera_panel.start_detection.connect(self.start_detection)
        self.camera_panel.stop_detection.connect(self.stop_detection)
        self.camera_panel.toggle_privacy.connect(self.toggle_privacy)

    def update_camera(self, frame):
        # Only update camera if detection is running
        if self.is_detecting:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()

            pixmap = QPixmap.fromImage(q_image)
            # Scale to fit camera panel size
            scaled_pixmap = pixmap.scaled(720, 540, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.camera_panel.update_camera_frame(scaled_pixmap)

    def update_detection(self, data):
        # Update visual flash state
        regions_with_contact = data.get("regions_with_contact", [])
        region_details = data.get("region_details", {})
        alerts_active = data.get("alerts_active", [])

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
            # Alert ended (potential mindful stop)
            self.mindful_stops += 1

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
        session_minutes = self._get_session_minutes()
        self.camera_panel.update_stats(self.total_detections, session_minutes, self.mindful_stops)

    def start_detection(self):
        """Start detection process"""
        if self.camera_thread.start_detection():
            self.is_detecting = True
            self.session_start_time = time.time()
            self.total_detections = 0
            self.mindful_stops = 0
            self.last_alert_state = False

            # Start session timer
            self.session_timer.start(1000)  # Update every second

            # Update UI
            self.camera_panel.set_detection_state(True)
            self.status_badge.set_status("detecting")

    def stop_detection(self):
        """Stop detection process"""
        self.camera_thread.stop_detection()
        self.is_detecting = False
        self.session_start_time = None

        # Stop session timer
        self.session_timer.stop()

        # Update UI
        self.camera_panel.set_detection_state(False)
        self.status_badge.set_status("ready")
        self.show_feed = True
        self.set_flash_state("none")

    def toggle_privacy(self):
        """Toggle camera feed visibility without stopping detection"""
        self.show_feed = not self.show_feed
        self.camera_panel.set_privacy_state(self.show_feed)

    def set_flash_state(self, state):
        """Update flash state with glass theme"""
        if state == self.current_flash_state:
            return

        self.current_flash_state = state

        if state == "red":
            # Red overlay for alerts
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: {Theme.BACKGROUND};
                }}
                QMainWindow::after {{
                    background: rgba(231, 76, 60, 0.2);
                }}
            """)
        elif state == "orange":
            # Orange overlay for proximity
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: {Theme.BACKGROUND};
                }}
                QMainWindow::after {{
                    background: rgba(255, 152, 0, 0.15);
                }}
            """)
        else:
            # Normal glass background
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: {Theme.BACKGROUND};
                }}
            """)

    def toggle_region(self, region: str, enabled: bool):
        """Handle region toggle from settings panel"""
        if self.camera_thread.detector:
            self.camera_thread.detector.toggle_region(region)

    def update_contact_duration(self, duration: float):
        """Handle contact duration change from settings panel"""
        Config.update_contact_duration(duration)

    def _update_session_timer(self):
        """Update session timer display"""
        if self.is_detecting and self.session_start_time:
            session_minutes = self._get_session_minutes()
            self.camera_panel.update_stats(self.total_detections, session_minutes, self.mindful_stops)

    def _get_session_minutes(self):
        """Get current session duration in minutes"""
        if self.session_start_time:
            elapsed = time.time() - self.session_start_time
            return int(elapsed // 60)
        return 0

    def _play_alert_sound(self):
        """Play alert sound - cooldown already handled by backend"""
        try:
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff", "-t", "0.35"])
        except Exception as e:
            print(f"Could not play sound: {e}")

    def closeEvent(self, event):
        if self.is_detecting:
            self.stop_detection()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
