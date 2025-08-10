#!/usr/bin/env python3
"""
Minimal PyQt6 Implementation of Mindful Touch
Camera feed with visual detection triggers only
"""

import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

from backend.detection.multi_region_detector import MultiRegionDetector


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


class StatusOverlay(QWidget):
    """Simple status overlay"""
    
    def __init__(self):
        super().__init__()
        self.setFixedSize(180, 120)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 8px;
                color: white;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        self.hands_label = QLabel("Hands: --")
        self.face_label = QLabel("Face: --")
        self.contacts_label = QLabel("Contacts: 0")
        self.alerts_label = QLabel("Status: Ready")
        
        for label in [self.hands_label, self.face_label, self.contacts_label, self.alerts_label]:
            layout.addWidget(label)
        
    def update_status(self, data):
        self.hands_label.setText(f"Hands: {'✓' if data.get('hands_detected') else '✗'}")
        self.face_label.setText(f"Face: {'✓' if data.get('face_detected') else '✗'}")
        
        contacts = data.get('contact_points', 0)
        self.contacts_label.setText(f"Contacts: {contacts}")
        
        alerts = data.get('alerts_active', [])
        if alerts:
            self.alerts_label.setText(f"ALERT: {', '.join(alerts)}")
            self.setStyleSheet(self.styleSheet() + "QLabel { color: #ff6b6b; }")
        else:
            self.alerts_label.setText("Status: OK")
            self.setStyleSheet(self.styleSheet().replace("color: #ff6b6b;", ""))


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
        self.setMinimumSize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Mindful Touch")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
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
        
        layout.addWidget(camera_container)
        
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
        layout.addWidget(self.control_button)
        
    def connect_signals(self):
        self.camera_thread.frame_ready.connect(self.update_camera)
        self.camera_thread.detection_data.connect(self.update_detection)
        self.control_button.clicked.connect(self.toggle_detection)
        self.flash_timer.timeout.connect(self.stop_flash)
        
    def update_camera(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.camera_label.setPixmap(scaled_pixmap)
        
    def update_detection(self, data):
        self.overlay.update_status(data)
        
        # Flash on alerts
        if data.get('alerts_active'):
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