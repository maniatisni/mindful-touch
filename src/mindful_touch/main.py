"""Main CLI application for Mindful Touch."""

import signal
import sys
import time
from typing import Any, Optional, Tuple

import click
import cv2
import numpy as np

from .config import DetectionConfig, NotificationConfig, get_config, get_config_manager
from .detector import DetectionEvent, DetectionResult, HandFaceDetector
from .notifier import NotificationManager
from .ui.qt_gui import main_gui


class MindfulTouchApp:
    """Main application coordinating detection and notifications."""

    def __init__(self) -> None:
        self.config = get_config()
        self.detector = HandFaceDetector(self.config.detection, self.config.camera)
        self.notifier = NotificationManager(self.config.notifications)
        self.is_running: bool = False
        self.controls_visible: bool = True
        self.control_window_name: str = "Controls"

        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        signal.signal(signal.SIGTERM, lambda s, f: self.stop())

    def _create_control_panel(self, window_name: str) -> None:
        """Create interactive control panel with sliders."""
        if self.controls_visible:
            cv2.namedWindow(self.control_window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.control_window_name, 400, 600)

            # Detection parameters
            cv2.createTrackbar(
                "Sensitivity",
                self.control_window_name,
                int(self.config.detection.sensitivity * 100),
                100,
                self._on_sensitivity_change,
            )

            cv2.createTrackbar(
                "Hand-Face Threshold (cm)",
                self.control_window_name,
                int(self.config.detection.hand_face_threshold_cm),
                50,
                self._on_threshold_change,
            )

            cv2.createTrackbar(
                "Pinch Threshold (cm)",
                self.control_window_name,
                int(self.config.detection.pinching_threshold_cm * 10),
                100,
                self._on_pinch_threshold_change,
            )

            cv2.createTrackbar(
                "Confidence",
                self.control_window_name,
                int(self.config.detection.confidence_threshold * 100),
                95,
                self._on_confidence_change,
            )

            # Notification parameters
            cv2.createTrackbar(
                "Notification Enabled",
                self.control_window_name,
                1 if self.config.notifications.enabled else 0,
                1,
                self._on_notification_toggle,
            )

            cv2.createTrackbar(
                "Cooldown (s)",
                self.control_window_name,
                self.config.notifications.cooldown_seconds,
                300,
                self._on_cooldown_change,
            )

            cv2.createTrackbar(
                "Duration (s)",
                self.control_window_name,
                self.config.notifications.duration_seconds,
                30,
                self._on_duration_change,
            )

            # Create info panel
            self._update_control_display()

    def _update_control_display(self) -> None:
        """Update the control panel display with current values."""
        if not self.controls_visible:
            return

        # Create info image using numpy
        info_img: np.ndarray = 255 * np.ones((400, 400, 3), dtype=np.uint8)

        # Add text overlay with current values
        font: int = cv2.FONT_HERSHEY_SIMPLEX
        y_pos: int = 30
        line_height: int = 25

        texts: list[str] = [
            "=== DETECTION PARAMETERS ===",
            f"Sensitivity: {self.config.detection.sensitivity:.2f}",
            f"Hand-Face Threshold: {self.config.detection.hand_face_threshold_cm:.1f}cm",
            f"Pinch Threshold: {getattr(self.config.detection, 'pinching_threshold_cm', 2.5):.1f}cm",
            f"Confidence: {self.config.detection.confidence_threshold:.2f}",
            "",
            "=== NOTIFICATION SETTINGS ===",
            f"Enabled: {'Yes' if self.config.notifications.enabled else 'No'}",
            f"Cooldown: {self.config.notifications.cooldown_seconds}s",
            f"Duration: {self.config.notifications.duration_seconds}s",
            "",
            "=== CONTROLS ===",
            "Press 'c' to toggle this panel",
            "Press 'r' to reset to defaults",
            "Press 's' to save settings",
            "Press 'q' or ESC to quit",
        ]

        for i, text in enumerate(texts):
            color: Tuple[int, int, int] = (0, 255, 255) if text.startswith("===") else (255, 255, 255)
            cv2.putText(info_img, text, (10, y_pos + i * line_height), font, 0.5, color, 1, cv2.LINE_AA)

        cv2.imshow(self.control_window_name, info_img)

    def _on_sensitivity_change(self, val: int) -> None:
        """Callback for sensitivity slider."""
        self.config.detection.sensitivity = val / 100.0
        self._update_control_display()

    def _on_threshold_change(self, val: int) -> None:
        """Callback for hand-face threshold slider."""
        self.config.detection.hand_face_threshold_cm = float(val)
        self._update_control_display()

    def _on_pinch_threshold_change(self, val: int) -> None:
        """Callback for pinch threshold slider."""
        if hasattr(self.config.detection, "pinching_threshold_cm"):
            self.config.detection.pinching_threshold_cm = val / 10.0
        self._update_control_display()

    def _on_confidence_change(self, val: int) -> None:
        """Callback for confidence threshold slider."""
        self.config.detection.confidence_threshold = val / 100.0
        self._update_control_display()

    def _on_notification_toggle(self, val: int) -> None:
        """Callback for notification enable/disable."""
        self.config.notifications.enabled = bool(val)
        self._update_control_display()

    def _on_cooldown_change(self, val: int) -> None:
        """Callback for notification cooldown slider."""
        self.config.notifications.cooldown_seconds = val
        self._update_control_display()

    def _on_duration_change(self, val: int) -> None:
        """Callback for notification duration slider."""
        self.config.notifications.duration_seconds = val
        self._update_control_display()

    def _toggle_controls(self) -> None:
        """Toggle visibility of control panel."""
        self.controls_visible = not self.controls_visible
        if self.controls_visible:
            self._create_control_panel("Mindful Touch")
        else:
            cv2.destroyWindow(self.control_window_name)

    def _reset_to_defaults(self) -> None:
        """Reset all parameters to default values."""
        self.config.detection = DetectionConfig()
        self.config.notifications = NotificationConfig()

        # Update trackbars
        if self.controls_visible:
            cv2.setTrackbarPos("Sensitivity", self.control_window_name, int(self.config.detection.sensitivity * 100))
            cv2.setTrackbarPos(
                "Hand-Face Threshold (cm)",
                self.control_window_name,
                int(self.config.detection.hand_face_threshold_cm),
            )
            cv2.setTrackbarPos(
                "Pinch Threshold (cm)",
                self.control_window_name,
                int(getattr(self.config.detection, "pinching_threshold_cm", 2.5) * 10),
            )
            cv2.setTrackbarPos(
                "Confidence", self.control_window_name, int(self.config.detection.confidence_threshold * 100)
            )
            cv2.setTrackbarPos(
                "Notification Enabled", self.control_window_name, 1 if self.config.notifications.enabled else 0
            )
            cv2.setTrackbarPos("Cooldown (s)", self.control_window_name, self.config.notifications.cooldown_seconds)
            cv2.setTrackbarPos("Duration (s)", self.control_window_name, self.config.notifications.duration_seconds)

        self._update_control_display()
        print("🔄 Reset to default settings")

    def _save_settings(self) -> None:
        """Save current settings to config file."""
        manager = get_config_manager()
        manager.save_config(self.config)
        print("💾 Settings saved")

    def run(self, show_live_feed: bool = False) -> None:
        """Run the main monitoring loop with optional interactive controls."""
        if not self.detector.initialize_camera():
            print("❌ Failed to initialize camera")
            return

        self.is_running = True
        print("👁️ Monitoring active...")

        if show_live_feed:
            cv2.namedWindow("Mindful Touch", cv2.WINDOW_NORMAL)
            self._create_control_panel("Mindful Touch")
            print("\n🎛️ Interactive Controls:")
            print("  'c' - Toggle control panel")
            print("  'r' - Reset to defaults")
            print("  's' - Save current settings")
            print("  'q' or ESC - Quit")

        try:
            while self.is_running:
                # Update detector with current config (in case sliders changed values)
                self.detector.detection_config = self.config.detection
                self.notifier.config = self.config.notifications

                result: Optional[DetectionResult] = self.detector.capture_and_detect()
                if not result:
                    time.sleep(0.001)
                    continue

                # Handle detection events
                if result.event == DetectionEvent.HAND_NEAR_FACE:
                    if self.notifier.show_mindful_moment():
                        print(f"🌸 Mindful moment (distance: {result.min_hand_face_distance_cm:.1f}cm)")
                    else:
                        cooldown: float = self.notifier.get_cooldown_remaining()
                        if cooldown > 0:
                            print(f"🔇 Cooldown: {cooldown:.1f}s")
                elif result.event == DetectionEvent.EYEBROW_PINCH:
                    self.notifier._show_notification(
                        title="Eyebrow Pinch Detected", message="Stop touching your eyebrows!❤️"
                    )
                    print(f"⚠️ Eyebrow pinching detected! (distance: {result.min_hand_face_distance_cm:.1f}cm)")
                elif result.event == DetectionEvent.SCALP_PINCH:
                    self.notifier._show_notification(
                        title="Scalp/Temple Pinch Detected", message="Stop pinching your scalp/temple!❤️"
                    )
                    print(f"⚠️ Scalp/temple pinching detected! (distance: {result.min_hand_face_distance_cm:.1f}cm)")

                # Show live feed with enhanced annotations
                if show_live_feed and self.detector.cap:
                    ret: bool
                    frame: Optional[np.ndarray]
                    ret, frame = self.detector.cap.read()
                    if ret and frame is not None and result:
                        annotated: np.ndarray = self.detector.get_annotated_frame(frame, result)

                        # Add parameter overlay to main window
                        cv2.putText(
                            annotated,
                            f"Sensitivity: {self.config.detection.sensitivity:.2f}",
                            (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (200, 200, 200),
                            1,
                        )
                        cv2.putText(
                            annotated,
                            f"Threshold: {self.config.detection.hand_face_threshold_cm:.1f}cm",
                            (20, 140),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (200, 200, 200),
                            1,
                        )
                        cv2.putText(
                            annotated,
                            f"Pinch: {getattr(self.config.detection, 'pinching_threshold_cm', 2.5):.1f}cm",
                            (20, 160),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (200, 200, 200),
                            1,
                        )

                        cv2.imshow("Mindful Touch", annotated)

                        # Handle key presses
                        key: int = cv2.waitKey(1) & 0xFF
                        if key == ord("q") or key == 27:  # 'q' or ESC
                            break
                        elif key == ord("c"):  # Toggle controls
                            self._toggle_controls()
                        elif key == ord("r"):  # Reset to defaults
                            self._reset_to_defaults()
                        elif key == ord("s"):  # Save settings
                            self._save_settings()

                # Adaptive sleep
                sleep_time: float = max(
                    0.001,
                    (self.config.detection.detection_interval_ms - result.processing_time_ms) / 1000,
                )
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop application and cleanup."""
        self.is_running = False
        self.detector.cleanup()
        cv2.destroyAllWindows()
        print("\n✅ Stopped")


@click.group()
def cli() -> None:
    """Mindful Touch - Hand movement awareness tool."""
    pass


@cli.command()
@click.option("--live-feed", is_flag=True, help="Show live camera feed with interactive controls")
@click.option("--sensitivity", type=click.FloatRange(0.1, 1.0), help="Detection sensitivity")
@click.option("--threshold", type=click.FloatRange(5.0, 50.0), help="Distance threshold (cm)")
def start(live_feed: bool, sensitivity: Optional[float], threshold: Optional[float]) -> None:
    """Start monitoring with optional interactive controls."""
    app: MindfulTouchApp = MindfulTouchApp()

    # Apply overrides
    if sensitivity is not None:
        app.config.detection.sensitivity = sensitivity
    if threshold is not None:
        app.config.detection.hand_face_threshold_cm = threshold

    app.run(show_live_feed=live_feed)


@cli.command()
@click.option("--duration", type=int, default=10, help="Calibration duration (seconds)")
def calibrate(duration: int) -> None:
    """Calibrate detection thresholds."""
    config = get_config()
    detector: HandFaceDetector = HandFaceDetector(config.detection, config.camera)

    print(f"🎯 Calibrating for {duration} seconds...")
    print("   Sit normally and keep hands visible")

    results: dict[str, Any] = detector.calibrate(duration)

    if "error" in results:
        print(f"❌ {results['error']}")
        return

    print("\n✅ Results:")
    print(f"   Samples: {results['samples']}")
    print(f"   Average distance: {results['avg_distance']:.1f}cm")
    print(f"   Suggested threshold: {results['suggested_threshold']:.1f}cm")

    if click.confirm(f"\nApply threshold of {results['suggested_threshold']:.1f}cm?"):
        manager = get_config_manager()
        manager.update_config(detection={"hand_face_threshold_cm": results["suggested_threshold"]})
        print("✅ Threshold updated")


@cli.command()
def test() -> None:
    """Test camera and notifications."""
    config = get_config()

    # Test notifications
    print("🔔 Testing notifications...")
    notifier: NotificationManager = NotificationManager(config.notifications)
    if notifier.test_notification():
        print("✅ Notifications working")
    else:
        print("❌ Notification test failed")

    # Test camera
    print("\n📷 Testing camera...")
    detector: HandFaceDetector = HandFaceDetector(config.detection, config.camera)
    if detector.initialize_camera():
        print(f"✅ Camera {config.camera.device_id} working")
        detector.cleanup()
    else:
        print(f"❌ Camera {config.camera.device_id} not working")


@cli.command()
@click.option("--sensitivity", type=click.FloatRange(0.1, 1.0))
@click.option("--threshold", type=click.FloatRange(2.0, 50.0))
@click.option("--cooldown", type=click.IntRange(5, 300))
@click.option("--camera-id", type=int)
@click.option("--pinching-threshold", type=click.FloatRange(0.5, 10.0))
def config(
    sensitivity: Optional[float],
    threshold: Optional[float],
    pinching_threshold: Optional[float],
    cooldown: Optional[int],
    camera_id: Optional[int],
) -> None:
    """View or update configuration."""
    manager = get_config_manager()
    current = get_config()

    updates: dict[str, dict[str, Any]] = {}
    if sensitivity is not None:
        updates.setdefault("detection", {})["sensitivity"] = sensitivity
    if threshold is not None:
        updates.setdefault("detection", {})["hand_face_threshold_cm"] = threshold
    if cooldown is not None:
        updates.setdefault("notifications", {})["cooldown_seconds"] = cooldown
    if camera_id is not None:
        updates.setdefault("camera", {})["device_id"] = camera_id
    if pinching_threshold is not None:
        updates.setdefault("detection", {})["pinching_threshold_cm"] = pinching_threshold

    if updates:
        manager.update_config(**updates)
        print("✅ Configuration updated")

    print("\n📋 Current Configuration:")
    print(f"   Sensitivity: {current.detection.sensitivity}")
    print(f"   Threshold: {current.detection.hand_face_threshold_cm}cm")
    print(f"   Cooldown: {current.notifications.cooldown_seconds}s")
    print(f"   Camera ID: {current.camera.device_id}")
    print(f"   Pinching Threshold: {getattr(current.detection, 'pinching_threshold_cm', 2.5)}cm")


@cli.command()
def list_cameras() -> None:
    """List available cameras."""
    print("🔍 Searching for cameras...")

    found: list[int] = []
    for i in range(10):
        cap: cv2.VideoCapture = cv2.VideoCapture(i)
        if cap.isOpened():
            width: int = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height: int = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps: int = int(cap.get(cv2.CAP_PROP_FPS))

            print(f"\n📷 Camera {i}: {width}x{height} @ {fps}fps")
            found.append(i)
        cap.release()

    if not found:
        print("❌ No cameras found")
    else:
        print(f"\n✅ Found {len(found)} camera(s)")


@cli.command()
def gui():
    """Launch the GUI application."""
    main_gui()


def main() -> None:
    """Entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
