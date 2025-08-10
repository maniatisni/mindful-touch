"""Camera display widget with detection overlay."""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont, QPainter, QColor, QBrush
import cv2


class DetectionOverlay(QFrame):
    """Overlay widget showing detection status information."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.update_data({})
        
    def setup_ui(self):
        self.setFixedSize(240, 140)
        self.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.8);
                border-radius: 8px;
                padding: 12px;
                color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        # Status labels with fixed widths
        self.hands_label = QLabel("Hands: Not detected")
        self.hands_label.setFixedWidth(180)
        self.hands_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        
        self.face_label = QLabel("Face: Not detected")
        self.face_label.setFixedWidth(180)
        self.face_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        
        self.contacts_label = QLabel("Contacts: 0")
        self.contacts_label.setFixedWidth(180)
        self.contacts_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        
        self.alert_label = QLabel("No alerts")
        self.alert_label.setFixedWidth(180)
        self.alert_label.setStyleSheet("font-family: monospace; font-size: 12px;")
        
        layout.addWidget(self.hands_label)
        layout.addWidget(self.face_label)
        layout.addWidget(self.contacts_label)
        layout.addWidget(self.alert_label)
        
    def update_data(self, detection_data: dict):
        """Update overlay with new detection data."""
        # Hands status
        hands_detected = detection_data.get('hands_detected', False)
        self.hands_label.setText(f"Hands: {'Detected ✓' if hands_detected else 'Not detected ✗'}")
        self.hands_label.setStyleSheet(f"""
            font-family: monospace; 
            font-size: 12px; 
            color: {'#10b981' if hands_detected else '#ef4444'};
        """)
        
        # Face status
        face_detected = detection_data.get('face_detected', False)
        self.face_label.setText(f"Face: {'Detected ✓' if face_detected else 'Not detected ✗'}")
        self.face_label.setStyleSheet(f"""
            font-family: monospace; 
            font-size: 12px; 
            color: {'#10b981' if face_detected else '#ef4444'};
        """)
        
        # Contacts
        contacts = detection_data.get('contact_points', [])
        contact_count = len(contacts)
        self.contacts_label.setText(f"Contacts: {contact_count}")
        self.contacts_label.setStyleSheet(f"""
            font-family: monospace; 
            font-size: 12px; 
            color: {'#ef4444' if contact_count > 0 else '#10b981'};
        """)
        
        # Alerts
        alert_regions = detection_data.get('alert_regions', [])
        if alert_regions:
            self.alert_label.setText(f"Alert: {', '.join(alert_regions)}")
            self.alert_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #ef4444;")
        else:
            self.alert_label.setText("No alerts")
            self.alert_label.setStyleSheet("font-family: monospace; font-size: 12px; color: #10b981;")


class CameraDisplayWidget(QWidget):
    """Widget for displaying camera feed with detection overlay."""
    
    detection_toggle_requested = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.is_detecting = False
        self.current_frame = None
        self.alert_flash_timer = QTimer()
        self.alert_flash_timer.timeout.connect(self.clear_alert_flash)
        self.setup_ui()
        
    def setup_ui(self):
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Camera display area
        self.camera_container = QFrame()
        self.camera_container.setStyleSheet("""
            QFrame {
                background: #f7fafc;
                border: 2px dashed #cbd5e0;
                border-radius: 12px;
                position: relative;
            }
        """)
        
        camera_layout = QVBoxLayout(self.camera_container)
        camera_layout.setContentsMargins(20, 20, 20, 20)
        
        # Camera feed label
        self.camera_label = QLabel()
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumHeight(300)
        self.camera_label.setStyleSheet("border: none; background: transparent;")
        
        # Initial placeholder content
        self.show_placeholder()
        
        camera_layout.addWidget(self.camera_label)
        
        # Detection overlay (initially hidden)
        self.overlay = DetectionOverlay()
        self.overlay.setParent(self.camera_container)
        self.overlay.move(15, 15)  # Position at top-left
        self.overlay.hide()
        
        # Control buttons
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.toggle_button = QPushButton("Start Detection")
        self.toggle_button.setFixedSize(140, 44)
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a67d8, stop:1 #6b46c1);
            }
        """)
        self.toggle_button.clicked.connect(self.on_toggle_detection)
        controls_layout.addWidget(self.toggle_button)
        
        camera_layout.addLayout(controls_layout)
        layout.addWidget(self.camera_container)
        
    def show_placeholder(self):
        """Show placeholder content when no camera feed."""
        placeholder_layout = QVBoxLayout()
        placeholder_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Clear existing widget
        self.camera_label.clear()
        self.camera_label.setText("📹\n\nCamera feed will appear here")
        self.camera_label.setStyleSheet("""
            font-size: 48px;
            color: rgba(113, 128, 150, 0.5);
            line-height: 1.2;
            border: none;
            background: transparent;
        """)
        
    def on_toggle_detection(self):
        """Handle detection toggle button click."""
        new_state = not self.is_detecting
        self.detection_toggle_requested.emit(new_state)
        
    def set_detection_state(self, detecting: bool):
        """Update detection state and UI."""
        self.is_detecting = detecting
        
        if detecting:
            self.toggle_button.setText("Stop Detection")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #ef4444, stop:1 #dc2626);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #dc2626, stop:1 #b91c1c);
                }
            """)
            self.overlay.show()
        else:
            self.toggle_button.setText("Start Detection")
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #667eea, stop:1 #764ba2);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #5a67d8, stop:1 #6b46c1);
                }
            """)
            self.overlay.hide()
            self.show_placeholder()
            
    def update_frame(self, frame: np.ndarray):
        """Update camera display with new frame."""
        if frame is None:
            self.show_placeholder()
            return
            
        # Convert OpenCV frame to Qt pixmap
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        
        # Scale to fit label while maintaining aspect ratio
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.camera_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.camera_label.setPixmap(scaled_pixmap)
        self.current_frame = frame
        
    def update_detection_data(self, detection_data: dict):
        """Update detection overlay with new data."""
        self.overlay.update_data(detection_data)
        
        # Flash alert if there are contact points
        if detection_data.get('contact_points', []):
            self.flash_alert()
            
    def flash_alert(self):
        """Flash the camera container red for alert."""
        self.camera_container.setStyleSheet("""
            QFrame {
                background: rgba(239, 68, 68, 0.9);
                border: 2px solid #ef4444;
                border-radius: 12px;
            }
        """)
        
        # Clear flash after 200ms
        self.alert_flash_timer.stop()
        self.alert_flash_timer.start(200)
        
    def clear_alert_flash(self):
        """Clear the alert flash effect."""
        self.alert_flash_timer.stop()
        self.camera_container.setStyleSheet("""
            QFrame {
                background: #f7fafc;
                border: 2px dashed #cbd5e0;
                border-radius: 12px;
            }
        """)