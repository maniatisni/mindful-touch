#!/usr/bin/env python3
"""
Minimal PyQt6 Implementation of Mindful Touch
Camera feed with visual detection triggers only
"""

import sys

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from backend.detection.multi_region_detector import MultiRegionDetector
from backend.detection.config import Config
from ui import SettingsPanel, StatusOverlay


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
        self.flash_timer = QTimer()
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setWindowTitle("Mindful Touch")
        self.setMinimumSize(1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side - Camera and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Title
        title = QLabel("Mindful Touch")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        left_layout.addWidget(title)

        # Camera container
        camera_container = QWidget()
        camera_container.setMinimumSize(640, 480)
        container_layout = QVBoxLayout(camera_container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        # Camera label
        self.camera_label = QLabel("Camera will appear here\nClick Start to begin")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
                font-size: 16px;
                color: #666;
            }
        """)
        self.camera_label.setMinimumSize(640, 480)
        container_layout.addWidget(self.camera_label)

        # Overlay
        self.overlay = StatusOverlay()
        self.overlay.setParent(camera_container)
        self.overlay.move(10, 10)

        left_layout.addWidget(camera_container)

        # Control button
        self.control_button = QPushButton("Start Detection")
        self.control_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        left_layout.addWidget(self.control_button)

        # Right side - Settings panel
        self.settings_panel = SettingsPanel()
        self.settings_panel.setFixedWidth(250)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.settings_panel)

    def connect_signals(self):
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread.detection_data.connect(self.update_detection)
        self.control_button.clicked.connect(self.toggle_detection)
        self.flash_timer.timeout.connect(self.stop_flash)

        # Connect settings panel signals
        self.settings_panel.region_toggled.connect(self.toggle_region)
        self.settings_panel.contact_duration_changed.connect(self.update_contact_duration)

    def update_camera(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()

        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.camera_label.setPixmap(scaled_pixmap)

    def update_detection(self, data):
        self.overlay.update_status(data)

        # Flash on alerts
        if data.get("alerts_active"):
            self.start_flash()

    def toggle_detection(self):
        if not self.is_detecting:
            if self.camera_thread.start_detection():
                self.is_detecting = True
                self.control_button.setText("Stop Detection")
                self.control_button.setStyleSheet("""
                    QPushButton {
                        background-color: #f44336;
                        color: white;
                        border: none;
                        padding: 15px 30px;
                        font-size: 16px;
                        border-radius: 8px;
                        margin: 20px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """)
        else:
            self.camera_thread.stop_detection()
            self.is_detecting = False
            self.control_button.setText("Start Detection")
            self.control_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 8px;
                    margin: 20px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.camera_label.clear()
            self.camera_label.setText("Camera will appear here\nClick Start to begin")

    def start_flash(self):
        self.setStyleSheet("QMainWindow { background-color: rgba(255, 0, 0, 100); }")
        self.flash_timer.start(200)

    def stop_flash(self):
        self.flash_timer.stop()
        self.setStyleSheet("")

    def toggle_region(self, region: str, enabled: bool):
        """Handle region toggle from settings panel"""
        if self.camera_thread.detector:
            self.camera_thread.detector.toggle_region(region)

    def update_contact_duration(self, duration: float):
        """Handle contact duration change from settings panel"""
        Config.update_contact_duration(duration)

    def closeEvent(self, event):
        if self.is_detecting:
            self.camera_thread.stop_detection()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
