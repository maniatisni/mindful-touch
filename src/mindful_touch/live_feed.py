"""
Live feed visualization for Mindful Touch.

This module provides a real-time visualization window showing camera feed
with detection status and visual feedback.
"""

import threading
import time
from datetime import datetime
from typing import Optional

import cv2
import numpy as np

from .detector import DetectionResult, HandFaceDetector


class LiveFeedWindow:
    """Manages a live feed window showing real-time detection status."""

    def __init__(self, window_name: str = "Mindful Touch - Live Feed"):
        """Initialize the live feed window.

        Args:
            window_name: Name of the OpenCV window
        """
        self.window_name = window_name
        self.is_running = False
        self._display_thread: Optional[threading.Thread] = None
        self._detector: Optional[HandFaceDetector] = None
        self._last_pull_time: Optional[float] = None
        self._pull_count = 0
        self._session_start_time: Optional[float] = None

        # Visual feedback settings
        self.alert_duration = 2.0  # seconds to show alert
        self.alert_color = (0, 0, 255)  # Red for alerts
        self.normal_color = (0, 255, 0)  # Green for normal
        self.warning_color = (0, 165, 255)  # Orange for warning

    def set_detector(self, detector: HandFaceDetector) -> None:
        """Set the detector instance to get frames from.

        Args:
            detector: Hand-face detector instance
        """
        self._detector = detector

    def _create_status_overlay(
        self, frame: np.ndarray, result: Optional[DetectionResult]
    ) -> np.ndarray:
        """Create an overlay with status information.

        Args:
            frame: Base frame
            result: Latest detection result

        Returns:
            Frame with overlay
        """
        height, width = frame.shape[:2]
        overlay = frame.copy()

        # Create semi-transparent background for text
        cv2.rectangle(overlay, (0, 0), (width, 100), (0, 0, 0), -1)
        cv2.rectangle(overlay, (0, height - 60), (width, height), (0, 0, 0), -1)

        # Blend overlay
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

        if result:
            # Main status
            if result.is_hand_near_face:
                status_text = "⚠️ PULLING DETECTED!"
                text_color = self.alert_color
                self._last_pull_time = time.time()
                self._pull_count += 1
            else:
                status_text = "✓ Monitoring Active"
                text_color = self.normal_color

            # Flash effect for recent pulls
            if (
                self._last_pull_time
                and time.time() - self._last_pull_time < self.alert_duration
            ):
                # Create pulsing effect
                pulse = int(128 + 127 * np.sin(time.time() * 10))
                text_color = (0, 0, pulse)

                # Draw alert border
                cv2.rectangle(
                    frame, (5, 5), (width - 5, height - 5), self.alert_color, 3
                )

            # Draw main status
            cv2.putText(
                frame,
                status_text,
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.3,
                text_color,
                3,
            )

            # Draw distance if available
            if result.min_hand_face_distance_cm is not None:
                dist_text = f"Distance: {result.min_hand_face_distance_cm:.1f}cm"
                dist_color = (
                    self.alert_color
                    if result.min_hand_face_distance_cm < 10
                    else (
                        self.warning_color
                        if result.min_hand_face_distance_cm < 20
                        else (255, 255, 255)
                    )
                )
                cv2.putText(
                    frame,
                    dist_text,
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    dist_color,
                    2,
                )

            # Session statistics
            if self._session_start_time:
                session_duration = time.time() - self._session_start_time
                minutes = int(session_duration // 60)
                seconds = int(session_duration % 60)

                stats_text = (
                    f"Session: {minutes:02d}:{seconds:02d} | Pulls: {self._pull_count}"
                )
                cv2.putText(
                    frame,
                    stats_text,
                    (20, height - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                )

            # Detection info
            info_text = f"Face: {'Yes' if result.face_detected else 'No'} | Hands: {result.hands_detected}"
            cv2.putText(
                frame,
                info_text,
                (width - 250, height - 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2,
            )

        else:
            # No detection result
            cv2.putText(
                frame,
                "Waiting for detection...",
                (20, 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (128, 128, 128),
                2,
            )

        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(
            frame,
            timestamp,
            (width - 120, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        return frame

    def _display_loop(self):
        """Main display loop running in separate thread."""
        print("📺 Live feed window opened")

        # Create window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 800, 600)

        # Initialize session time
        self._session_start_time = time.time()

        # Placeholder frame
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(
            placeholder,
            "Initializing camera...",
            (150, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2,
        )

        last_frame = placeholder
        last_result = None

        while self.is_running:
            try:
                # Get latest frame from detector
                if self._detector:
                    frame = self._detector.get_live_frame()
                    if frame is not None:
                        last_frame = frame
                        # Extract result from detector's queue
                        result = (
                            self._detector._result_queue.queue[-1]
                            if self._detector._result_queue.qsize() > 0
                            else last_result
                        )
                        last_result = result
                    else:
                        # Use last frame if no new frame
                        frame = last_frame
                        result = last_result
                else:
                    frame = placeholder
                    result = None

                # Apply overlay
                display_frame = self._create_status_overlay(frame, result)

                # Show frame
                cv2.imshow(self.window_name, display_frame)

                # Check for window close
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:  # 'q' or ESC
                    print("📺 Live feed closed by user")
                    break
                elif key == ord("r"):  # Reset statistics
                    self._pull_count = 0
                    self._session_start_time = time.time()
                    print("📊 Statistics reset")

                # Check if window was closed
                if cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break

            except Exception as e:
                print(f"⚠️  Display error: {e}")
                time.sleep(0.1)

        # Cleanup
        cv2.destroyWindow(self.window_name)
        print("📺 Live feed window closed")

    def start(self) -> bool:
        """Start the live feed display.

        Returns:
            True if started successfully
        """
        if self.is_running:
            return False

        self.is_running = True
        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()
        return True

    def stop(self) -> None:
        """Stop the live feed display."""
        self.is_running = False

        if self._display_thread:
            self._display_thread.join(timeout=2.0)

        # Ensure window is destroyed
        try:
            cv2.destroyWindow(self.window_name)
        except:
            pass

    def reset_statistics(self) -> None:
        """Reset session statistics."""
        self._pull_count = 0
        self._session_start_time = time.time()
        self._last_pull_time = None


def create_live_feed_window() -> LiveFeedWindow:
    """Create a new live feed window instance.

    Returns:
        Configured live feed window
    """
    return LiveFeedWindow()
