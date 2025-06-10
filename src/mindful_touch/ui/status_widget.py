"""Status widget for the GUI."""

import time

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class StatusWidget(QWidget):
    """Widget for displaying session status."""

    def __init__(self):
        super().__init__()
        self.session_start_time = None
        self.detection_count = 0
        self.setup_ui()

        # Timer for updating session time
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_session_time)

    def setup_ui(self):
        """Setup the status UI."""
        layout = QVBoxLayout(self)

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

        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)

    def start_session(self):
        """Start a new session."""
        self.session_start_time = time.time()
        self.detection_count = 0

        self.status_indicator.setStyleSheet("color: #27ae60;")
        self.status_text.setText("Session Active - Monitoring")
        self.detection_count_label.setText("Detections: 0")

        self.update_timer.start(1000)  # Update every second

    def stop_session(self):
        """Stop the current session."""
        self.session_start_time = None

        self.status_indicator.setStyleSheet("color: #e74c3c;")
        self.status_text.setText("Session Inactive")

        self.update_timer.stop()

    def add_detection(self, distance: float):
        """Add a detection event."""
        self.detection_count += 1
        self.detection_count_label.setText(f"Detections: {self.detection_count}")

    def update_session_time(self):
        """Update session time display."""
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            minutes, seconds = divmod(elapsed, 60)
            self.session_time_label.setText(f"Session time: {minutes:02d}:{seconds:02d}")

    def show_progress(self, text: str):
        """Show progress bar with text."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_text.setText(text)

    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)
