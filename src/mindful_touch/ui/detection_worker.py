"""Detection worker for GUI."""

import time

from PySide6.QtCore import QObject, Signal

from ..detector import DetectionEvent, HandFaceDetector
from ..notifier import NotificationManager


class DetectionWorker(QObject):
    """Worker thread for hand detection."""

    detection_occurred = Signal(float)  # distance
    error_occurred = Signal(str)
    status_update = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.detector = None
        self.notifier = None
        self.running = False
        self._cooldown_until = 0  # Track cooldown end time

    def start_detection(self):
        """Start the detection process."""
        try:
            self.detector = HandFaceDetector(self.config.detection, self.config.camera)
            self.notifier = NotificationManager(self.config.notifications)

            if not self.detector.initialize_camera():
                self.error_occurred.emit("Failed to initialize camera")
                return

            self.running = True
            self.status_update.emit("Detection started")

            alert_active_since = None

            while self.running:
                # Update configs (in case GUI changed them)
                self.detector.detection_config = self.config.detection
                self.notifier.config = self.config.notifications

                # Check cooldown before detection (no events counted during cooldown)
                now = time.time()
                if self.notifier._is_in_cooldown():
                    alert_active_since = None  # Reset alert delay tracking
                    time.sleep(0.1)
                    continue

                result = self.detector.capture_and_detect()
                if not result:
                    time.sleep(0.001)
                    continue

                # Alert delay logic: require pulling to be detected for alert_delay seconds
                alert_delay = getattr(self.config.detection, "alert_delay_seconds", 0.5)
                if result.event == DetectionEvent.PULLING_DETECTED:
                    if alert_active_since is None:
                        alert_active_since = now
                    elif now - alert_active_since >= alert_delay:
                        self.detection_occurred.emit(result.min_hand_face_distance_cm or 0)
                        if self.notifier.show_mindful_moment():
                            print(f"🌸 Pulling detected (distance: {result.min_hand_face_distance_cm:.1f}cm)")
                        alert_active_since = None  # Reset after event
                else:
                    alert_active_since = None

                # Adaptive sleep
                sleep_time = max(
                    0.001,
                    (self.config.detection.detection_interval_ms - result.processing_time_ms) / 1000,
                )
                time.sleep(sleep_time)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if self.detector:
                self.detector.cleanup()
            self.status_update.emit("Detection stopped")

    def stop_detection(self):
        """Stop the detection process."""
        self.running = False
