#!/usr/bin/env python3
"""
Minimal PyQt6 Implementation of Mindful Touch
Camera feed with visual detection triggers only
"""

import sys

import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from backend.detection.config import Config
from backend.detection.multi_region_detector import MultiRegionDetector
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
        self.show_feed = True
        self.current_flash_state = "none"  # Track current flash state
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

        # Control buttons
        button_layout = QHBoxLayout()

        self.control_button = QPushButton("Start Detection")
        self.control_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        self.privacy_button = QPushButton("Hide Feed")
        self.privacy_button.setEnabled(False)  # Disabled until detection starts
        self.privacy_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)

        button_layout.addWidget(self.control_button)
        button_layout.addWidget(self.privacy_button)
        left_layout.addLayout(button_layout)

        # Right side - Settings panel
        self.settings_panel = SettingsPanel()
        self.settings_panel.setFixedWidth(250)

        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.settings_panel)

    def connect_signals(self):
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread.detection_data.connect(self.update_detection)
        self.control_button.clicked.connect(self.toggle_detection)
        self.privacy_button.clicked.connect(self.toggle_privacy)

        # Connect settings panel signals
        self.settings_panel.region_toggled.connect(self.toggle_region)
        self.settings_panel.contact_duration_changed.connect(self.update_contact_duration)

    def update_camera(self, frame):
        if self.show_feed:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()

            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.camera_label.setPixmap(scaled_pixmap)

    def update_detection(self, data):
        self.overlay.update_status(data)

        # Simplified hierarchical flash system
        alerts_active = data.get("alerts_active", [])
        regions_with_contact = data.get("regions_with_contact", [])

        if alerts_active:
            # Red background - persistent while alert is active
            self.set_flash_state("red")
        elif regions_with_contact:
            # Orange flash - brief flash for proximity
            self.set_flash_state("orange")
        else:
            # No contact - clear background
            self.set_flash_state("none")

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
                        margin: 10px;
                    }
                    QPushButton:hover {
                        background-color: #da190b;
                    }
                """)
                self.privacy_button.setEnabled(True)
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
            self.privacy_button.setEnabled(False)
            self.privacy_button.setText("Hide Feed")
            self.show_feed = True  # Reset to show feed
            self.camera_label.clear()
            self.camera_label.setText("Camera will appear here\nClick Start to begin")

    def toggle_privacy(self):
        """Toggle camera feed visibility without stopping detection"""
        self.show_feed = not self.show_feed

        if self.show_feed:
            self.privacy_button.setText("Hide Feed")
            self.privacy_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 8px;
                    margin: 10px;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
        else:
            self.privacy_button.setText("Show Feed")
            self.privacy_button.setStyleSheet("""
                QPushButton {
                    background-color: #607D8B;
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    font-size: 16px;
                    border-radius: 8px;
                    margin: 10px;
                }
                QPushButton:hover {
                    background-color: #546E7A;
                }
            """)
            # Show privacy message when feed is hidden
            self.camera_label.clear()
            self.camera_label.setText("🔒 Privacy Mode Active\nDetection running in background\nClick 'Show Feed' to view camera")
            self.camera_label.setStyleSheet(self.camera_label.styleSheet() + "font-size: 18px; color: #666;")

    def set_flash_state(self, state):
        """Simple persistent flash state - no timers"""
        if state == self.current_flash_state:
            return  # No change needed

        self.current_flash_state = state

        if state == "red":
            # Red background - persistent while alert active
            self.setStyleSheet("QMainWindow { background-color: rgba(255, 0, 0, 100); }")
        elif state == "orange":
            # Orange background - persistent while in proximity
            self.setStyleSheet("QMainWindow { background-color: rgba(255, 165, 0, 80); }")
        else:  # state == "none"
            # Clear background
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
