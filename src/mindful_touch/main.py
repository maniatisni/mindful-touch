"""Main CLI application for Mindful Touch."""

import signal
import sys
import time
from typing import Optional

import click
import cv2

from .config import get_config, get_config_manager
from .detector import HandFaceDetector, DetectionEvent
from .notifier import NotificationManager


class MindfulTouchApp:
    """Main application coordinating detection and notifications."""
    
    def __init__(self):
        self.config = get_config()
        self.detector = HandFaceDetector(self.config.detection, self.config.camera)
        self.notifier = NotificationManager(self.config.notifications)
        self.is_running = False
        
        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        signal.signal(signal.SIGTERM, lambda s, f: self.stop())
    
    def run(self, show_live_feed: bool = False):
        """Run the main monitoring loop."""
        if not self.detector.initialize_camera():
            print("❌ Failed to initialize camera")
            return
        
        self.is_running = True
        print("👁️  Monitoring active...")
        
        if show_live_feed:
            cv2.namedWindow("Mindful Touch", cv2.WINDOW_NORMAL)
        
        try:
            while self.is_running:
                result = self.detector.capture_and_detect()
                if not result:
                    time.sleep(0.001)
                    continue
                
                # Handle detection events
                if result.event == DetectionEvent.HAND_NEAR_FACE:
                    if self.notifier.show_mindful_moment():
                        print(f"🌸 Mindful moment (distance: {result.min_hand_face_distance_cm:.1f}cm)")
                    else:
                        cooldown = self.notifier.get_cooldown_remaining()
                        if cooldown > 0:
                            print(f"🔇 Cooldown: {cooldown:.1f}s")
                
                # Show live feed
                if show_live_feed:
                    ret, frame = self.detector.cap.read()
                    if ret and result:
                        annotated = self.detector.get_annotated_frame(frame, result)
                        cv2.imshow("Mindful Touch", annotated)
                        
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord('q') or key == 27:
                            break
                
                # Adaptive sleep
                sleep_time = max(0.001, (self.config.detection.detection_interval_ms - result.processing_time_ms) / 1000)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self):
        """Stop application and cleanup."""
        self.is_running = False
        self.detector.cleanup()
        cv2.destroyAllWindows()
        print("\n✅ Stopped")


@click.group()
def cli():
    """Mindful Touch - Hand movement awareness tool."""
    pass


@cli.command()
@click.option('--live-feed', is_flag=True, help='Show live camera feed')
@click.option('--sensitivity', type=click.FloatRange(0.1, 1.0), help='Detection sensitivity')
@click.option('--threshold', type=click.FloatRange(5.0, 50.0), help='Distance threshold (cm)')
def start(live_feed, sensitivity, threshold):
    """Start monitoring."""
    app = MindfulTouchApp()
    
    # Apply overrides
    if sensitivity:
        app.config.detection.sensitivity = sensitivity
    if threshold:
        app.config.detection.hand_face_threshold_cm = threshold
    
    app.run(show_live_feed=live_feed)


@cli.command()
@click.option('--duration', type=int, default=10, help='Calibration duration (seconds)')
def calibrate(duration):
    """Calibrate detection thresholds."""
    config = get_config()
    detector = HandFaceDetector(config.detection, config.camera)
    
    print(f"🎯 Calibrating for {duration} seconds...")
    print("   Sit normally and keep hands visible")
    
    results = detector.calibrate(duration)
    
    if 'error' in results:
        print(f"❌ {results['error']}")
        return
    
    print(f"\n✅ Results:")
    print(f"   Samples: {results['samples']}")
    print(f"   Average distance: {results['avg_distance']:.1f}cm")
    print(f"   Suggested threshold: {results['suggested_threshold']:.1f}cm")
    
    if click.confirm(f"\nApply threshold of {results['suggested_threshold']:.1f}cm?"):
        manager = get_config_manager()
        manager.update_config(detection={'hand_face_threshold_cm': results['suggested_threshold']})
        print("✅ Threshold updated")


@cli.command()
def test():
    """Test camera and notifications."""
    config = get_config()
    
    # Test notifications
    print("🔔 Testing notifications...")
    notifier = NotificationManager(config.notifications)
    if notifier.test_notification():
        print("✅ Notifications working")
    else:
        print("❌ Notification test failed")
    
    # Test camera
    print("\n📷 Testing camera...")
    detector = HandFaceDetector(config.detection, config.camera)
    if detector.initialize_camera():
        print(f"✅ Camera {config.camera.device_id} working")
        detector.cleanup()
    else:
        print(f"❌ Camera {config.camera.device_id} not working")


@cli.command()
@click.option('--sensitivity', type=click.FloatRange(0.1, 1.0))
@click.option('--threshold', type=click.FloatRange(2.0, 50.0))
@click.option('--cooldown', type=click.IntRange(5, 300))
@click.option('--camera-id', type=int)
def config(sensitivity, threshold, cooldown, camera_id):
    """View or update configuration."""
    manager = get_config_manager()
    current = get_config()
    
    updates = {}
    if sensitivity:
        updates.setdefault('detection', {})['sensitivity'] = sensitivity
    if threshold:
        updates.setdefault('detection', {})['hand_face_threshold_cm'] = threshold
    if cooldown:
        updates.setdefault('notifications', {})['cooldown_seconds'] = cooldown
    if camera_id is not None:
        updates.setdefault('camera', {})['device_id'] = camera_id
    
    if updates:
        manager.update_config(**updates)
        print("✅ Configuration updated")
    
    print("\n📋 Current Configuration:")
    print(f"   Sensitivity: {current.detection.sensitivity}")
    print(f"   Threshold: {current.detection.hand_face_threshold_cm}cm")
    print(f"   Cooldown: {current.notifications.cooldown_seconds}s")
    print(f"   Camera ID: {current.camera.device_id}")


@cli.command()
def list_cameras():
    """List available cameras."""
    print("🔍 Searching for cameras...")
    
    found = []
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            print(f"\n📷 Camera {i}: {width}x{height} @ {fps}fps")
            found.append(i)
            cap.release()
    
    if not found:
        print("❌ No cameras found")
    else:
        print(f"\n✅ Found {len(found)} camera(s)")


def main():
    """Entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


if __name__ == '__main__':
    main()