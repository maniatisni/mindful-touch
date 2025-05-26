"""
Main application for Mindful Touch - A gentle awareness tool for hand movement tracking.

This module provides the CLI interface and main application loop that coordinates
the detection system, notifications, and user configuration.
"""

import signal
import sys
import time
from pathlib import Path
from typing import Optional

import click

from .config import get_config, get_config_manager, AppConfig
from .detector import create_detector, DetectionEvent, HandFaceDetector
from .notifier import create_notification_manager, NotificationManager


class MindfulTouchApp:
    """Main application class that coordinates all components."""
    
    def __init__(self, config: AppConfig):
        """Initialize the Mindful Touch application.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.detector: Optional[HandFaceDetector] = None
        self.notifier: Optional[NotificationManager] = None
        self.is_running = False
        self._setup_signal_handlers()
        
        print("🌸 Mindful Touch - Gentle Awareness Tool")
        print("   Press Ctrl+C to stop gracefully")
    
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\n📝 Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self) -> bool:
        """Initialize all application components.
        
        Returns:
            True if initialization was successful
        """
        try:
            # Create detector
            print("🎯 Initializing hand-face detector...")
            self.detector = create_detector(
                self.config.detection,
                self.config.camera
            )
            
            # Create notification manager
            print("📱 Initializing notification system...")
            self.notifier = create_notification_manager(self.config.notifications)
            
            # Test notification system
            if self.config.notifications.enabled:
                print("🔔 Testing notification system...")
                if self.notifier.test_notification():
                    print("✅ Notification system working")
                else:
                    print("⚠️  Notification system may not be working properly")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def start_monitoring(self) -> None:
        """Start the main monitoring loop."""
        if not self.detector or not self.notifier:
            print("❌ Components not initialized. Call initialize() first.")
            return
        
        print("🚀 Starting monitoring...")
        
        # Start detection system
        if not self.detector.start_detection():
            print("❌ Failed to start detection system")
            return
        
        self.is_running = True
        
        # Statistics tracking
        frame_count = 0
        detection_count = 0
        start_time = time.time()
        last_stats_time = start_time
        
        try:
            print("👁️  Monitoring active - looking for hand-to-face movements...")
            
            while self.is_running:
                # Capture and process frame
                result = self.detector.capture_and_detect()
                
                if result is None:
                    time.sleep(0.1)
                    continue
                
                frame_count += 1
                
                # Handle detection events
                if result.event:
                    detection_count += 1
                    self._handle_detection_event(result.event, result)
                
                # Print periodic stats
                current_time = time.time()
                if current_time - last_stats_time >= 30:  # Every 30 seconds
                    self._print_stats(frame_count, detection_count, current_time - start_time)
                    last_stats_time = current_time
                
                # Sleep to maintain detection interval
                sleep_time = max(0, self.config.detection.detection_interval_ms / 1000)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
        finally:
            self.stop()
    
    def _handle_detection_event(self, event: DetectionEvent, result) -> None:
        """Handle a detection event by showing appropriate notifications.
        
        Args:
            event: The detection event that occurred
            result: Full detection result with details
        """
        if event == DetectionEvent.HAND_NEAR_FACE:
            # Main detection event - show mindful moment notification
            if self.notifier.show_mindful_moment():
                distance = result.min_hand_face_distance_cm
                print(f"🌸 Mindful moment triggered (distance: {distance:.1f}cm)")
            else:
                print(f"🔇 Detection suppressed (cooldown: {self.notifier.get_cooldown_remaining():.1f}s)")
        
        elif event == DetectionEvent.HAND_AWAY_FROM_FACE:
            # Optional: gentle positive reinforcement
            if self.config.notifications.enabled:
                print("✨ Hand moved away from face - well done!")
        
        elif event == DetectionEvent.FACE_LOST:
            print("👤 Face tracking lost")
        
        elif event == DetectionEvent.HAND_LOST:
            print("👋 Hand tracking lost")
    
    def _print_stats(self, frame_count: int, detection_count: int, elapsed_time: float) -> None:
        """Print monitoring statistics.
        
        Args:
            frame_count: Total frames processed
            detection_count: Total detections triggered
            elapsed_time: Time elapsed since start
        """
        fps = frame_count / elapsed_time if elapsed_time > 0 else 0
        detection_rate = detection_count / (elapsed_time / 60) if elapsed_time > 0 else 0
        
        print(f"📊 Stats: {frame_count} frames, {detection_count} detections, "
              f"{fps:.1f} FPS, {detection_rate:.1f} detections/min")
    
    def stop(self) -> None:
        """Stop the application and cleanup resources."""
        self.is_running = False
        
        if self.detector:
            self.detector.stop_detection()
        
        print("✅ Mindful Touch stopped gracefully")
    
    def calibrate(self, duration: int = 10) -> dict:
        """Run calibration mode.
        
        Args:
            duration: Calibration duration in seconds
            
        Returns:
            Calibration results
        """
        if not self.detector:
            print("❌ Detector not initialized")
            return {"error": "Detector not initialized"}
        
        return self.detector.calibrate(duration)


@click.group()
@click.option('--config-dir', type=click.Path(), help='Custom configuration directory')
@click.pass_context
def cli(ctx, config_dir):
    """Mindful Touch - A gentle awareness tool for mindful hand movement tracking.
    
    This tool helps you become more aware of unconscious hand-to-face movements
    through gentle desktop notifications. All processing happens locally on your device.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Load configuration
    try:
        if config_dir:
            # TODO: Allow custom config directory
            pass
        
        config = get_config()
        ctx.obj['config'] = config
        ctx.obj['config_manager'] = get_config_manager()
        
    except Exception as e:
        click.echo(f"❌ Failed to load configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--duration', type=int, default=10, 
              help='Debug monitoring duration in seconds')
@click.pass_context
def debug(ctx, duration):
    """Debug mode - shows detailed detection information."""
    config: AppConfig = ctx.obj['config']
    
    app = MindfulTouchApp(config)
    
    if not app.initialize():
        click.echo("❌ Failed to initialize application", err=True)
        sys.exit(1)
    
    if not app.detector.start_detection():
        click.echo("❌ Failed to start detection system", err=True)
        return
    
    click.echo(f"🔍 Debug mode for {duration} seconds...")
    click.echo("   Face=detected, Hands=count, Dist=distance_in_cm, Conf=confidence")
    
    start_time = time.time()
    frame_count = 0
    
    try:
        while time.time() - start_time < duration:
            result = app.detector.capture_and_detect()
            if result:
                frame_count += 1
                
                # Print every 10th frame to avoid spam
                if frame_count % 10 == 0:
                    elapsed = time.time() - start_time
                    dist_str = f"{result.min_hand_face_distance_cm:.1f}" if result.min_hand_face_distance_cm else "None"
                    click.echo(f"   {elapsed:4.1f}s: Face={result.face_detected}, "
                              f"Hands={result.hands_detected}, "
                              f"Dist={dist_str}cm, "
                              f"Conf={result.confidence:.2f}")
            
            time.sleep(0.1)
    
    finally:
        app.detector.stop_detection()
    
    click.echo(f"✅ Debug complete - processed {frame_count} frames")


@cli.command()
@click.option('--sensitivity', type=click.FloatRange(0.1, 1.0), 
              help='Detection sensitivity (0.1-1.0)')
@click.option('--threshold', type=click.FloatRange(5.0, 50.0), 
              help='Distance threshold in centimeters')
@click.option('--no-notifications', is_flag=True, 
              help='Disable notifications (monitoring only)')
@click.pass_context
def start(ctx, sensitivity, threshold, no_notifications):
    """Start monitoring for hand-to-face movements."""
    config: AppConfig = ctx.obj['config']
    
    # Apply command-line overrides
    if sensitivity is not None:
        config.detection.sensitivity = sensitivity
        click.echo(f"🎯 Sensitivity set to {sensitivity}")
    
    if threshold is not None:
        config.detection.hand_face_threshold_cm = threshold
        click.echo(f"📏 Threshold set to {threshold}cm")
    
    if no_notifications:
        config.notifications.enabled = False
        click.echo(f"🔇 Notifications disabled")
    
    # Create and run application
    app = MindfulTouchApp(config)
    
    if not app.initialize():
        click.echo("❌ Failed to initialize application", err=True)
        sys.exit(1)
    
    app.start_monitoring()


@cli.command()
@click.option('--duration', type=int, default=10, 
              help='Calibration duration in seconds')
@click.pass_context
def calibrate(ctx, duration):
    """Calibrate the detector for your setup."""
    config: AppConfig = ctx.obj['config']
    
    app = MindfulTouchApp(config)
    
    if not app.initialize():
        click.echo("❌ Failed to initialize application", err=True)
        sys.exit(1)
    
    click.echo(f"🎯 Starting calibration for {duration} seconds...")
    click.echo("   Please sit comfortably and look at the camera")
    click.echo("   Keep your hands in natural positions")
    
    results = app.calibrate(duration)
    
    if 'error' in results:
        click.echo(f"❌ Calibration failed: {results['error']}", err=True)
        if 'debug_info' in results:
            debug = results['debug_info']
            click.echo(f"   Debug: {debug['frames_processed']} frames processed")
            click.echo(f"   Suggestion: {debug['suggestion']}")
        click.echo("\n💡 Troubleshooting tips:")
        click.echo("   • Ensure good lighting")
        click.echo("   • Sit 50-100cm from camera")
        click.echo("   • Keep hands visible during calibration")
        click.echo("   • Try: mindful-touch test  # to verify camera works")
        return
    
    click.echo("\n✅ Calibration Results:")
    click.echo(f"   Samples collected: {results['samples']}")
    click.echo(f"   Average distance: {results['avg_distance']:.1f}cm")
    click.echo(f"   Suggested threshold: {results['suggested_threshold']:.1f}cm")
    
    # Ask if user wants to apply suggested threshold
    if click.confirm(f"\nApply suggested threshold of {results['suggested_threshold']:.1f}cm?"):
        config_manager = ctx.obj['config_manager']
        config_manager.update_config(
            detection={'hand_face_threshold_cm': results['suggested_threshold']}
        )
        click.echo("✅ Threshold updated and saved")


@cli.command()
@click.pass_context
def test(ctx):
    """Test the notification system."""
    config: AppConfig = ctx.obj['config']
    
    click.echo("🔔 Testing notification system...")
    
    notifier = create_notification_manager(config.notifications)
    
    if notifier.test_notification():
        click.echo("✅ Notification system is working!")
        click.echo(f"   Using: {notifier.provider_name}")
    else:
        click.echo("❌ Notification system is not working", err=True)
        click.echo("   Check your system's notification settings")


@cli.command()
@click.option('--sensitivity', type=click.FloatRange(0.1, 1.0))
@click.option('--threshold', type=click.FloatRange(2.0, 50.0))
@click.option('--cooldown', type=click.IntRange(5, 300))
@click.option('--message', type=str)
@click.option('--enable-notifications/--disable-notifications', default=None)
@click.pass_context
def config(ctx, sensitivity, threshold, cooldown, message, enable_notifications):
    """View or update configuration settings."""
    config_manager = ctx.obj['config_manager']
    current_config = ctx.obj['config']
    
    updates = {}
    
    # Collect updates
    if sensitivity is not None:
        updates.setdefault('detection', {})['sensitivity'] = sensitivity
    
    if threshold is not None:
        updates.setdefault('detection', {})['hand_face_threshold_cm'] = threshold
    
    if cooldown is not None:
        updates.setdefault('notifications', {})['cooldown_seconds'] = cooldown
    
    if message is not None:
        updates.setdefault('notifications', {})['message'] = message
    
    if enable_notifications is not None:
        updates.setdefault('notifications', {})['enabled'] = enable_notifications
    
    # Apply updates
    if updates:
        try:
            config_manager.update_config(**updates)
            click.echo("✅ Configuration updated successfully")
        except Exception as e:
            click.echo(f"❌ Failed to update configuration: {e}", err=True)
            return
    
    # Display current configuration
    click.echo("\n📋 Current Configuration:")
    click.echo(f"   Sensitivity: {current_config.detection.sensitivity}")
    click.echo(f"   Threshold: {current_config.detection.hand_face_threshold_cm}cm")
    click.echo(f"   Notifications: {'enabled' if current_config.notifications.enabled else 'disabled'}")
    click.echo(f"   Cooldown: {current_config.notifications.cooldown_seconds}s")
    click.echo(f"   Message: '{current_config.notifications.message}'")


@cli.command()
@click.confirmation_option(prompt='Are you sure you want to reset all settings?')
@click.pass_context
def reset(ctx):
    """Reset configuration to defaults."""
    config_manager = ctx.obj['config_manager']
    config_manager.reset_to_defaults()
    click.echo("✅ Configuration reset to defaults")


@cli.command()
@click.pass_context
def info(ctx):
    """Show system and configuration information."""
    config: AppConfig = ctx.obj['config']
    config_manager = ctx.obj['config_manager']
    
    click.echo("🌸 Mindful Touch - System Information")
    click.echo(f"   Version: 0.1.0")
    click.echo(f"   Config directory: {config_manager.config_dir}")
    click.echo(f"   Data directory: {config_manager.data_dir}")
    
    click.echo("\n📷 Camera Settings:")
    click.echo(f"   Device ID: {config.camera.device_id}")
    click.echo(f"   Resolution: {config.camera.width}x{config.camera.height}")
    click.echo(f"   FPS: {config.camera.fps}")
    
    click.echo("\n🎯 Detection Settings:")
    click.echo(f"   Sensitivity: {config.detection.sensitivity}")
    click.echo(f"   Threshold: {config.detection.hand_face_threshold_cm}cm")
    click.echo(f"   Confidence: {config.detection.confidence_threshold}")
    click.echo(f"   Interval: {config.detection.detection_interval_ms}ms")
    
    click.echo("\n🔔 Notification Settings:")
    click.echo(f"   Enabled: {config.notifications.enabled}")
    click.echo(f"   Title: '{config.notifications.title}'")
    click.echo(f"   Message: '{config.notifications.message}'")
    click.echo(f"   Duration: {config.notifications.duration_seconds}s")
    click.echo(f"   Cooldown: {config.notifications.cooldown_seconds}s")
    
    click.echo("\n🔒 Privacy Settings:")
    click.echo(f"   Save images: {config.privacy.save_images}")
    click.echo(f"   Log detections: {config.privacy.log_detections}")


def main():
    """Main entry point for the application."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()