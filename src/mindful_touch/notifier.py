"""Simplified cross-platform notification system."""

import platform
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional

from .config import NotificationConfig


class NotificationManager:
    """Manages desktop notifications with automatic method detection."""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self._last_notification_time: Optional[datetime] = None
        self.system = platform.system()
        self._working_method = self._detect_notification_method()

    def _detect_notification_method(self) -> Optional[str]:
        """Detect the best available notification method."""
        if self.system == "Darwin":  # macOS
            # Try osascript first (most reliable on macOS)
            try:
                subprocess.run(["osascript", "-e", ""], capture_output=True, timeout=1)
                return "osascript"
            except Exception:
                pass

            # Try pync as fallback (but handle it better)
            try:
                import pync

                # Test if pync actually works
                pync.notify("Test", title="Test", timeout=0.1)
                return "pync"
            except Exception:
                # pync often fails in packaged apps, continue to fallback
                pass

        elif self.system == "Linux":
            try:
                subprocess.run(["notify-send", "--version"], capture_output=True, timeout=1)
                return "notify-send"
            except Exception:
                pass

        elif self.system == "Windows":
            try:
                import win10toast

                return "win10toast"
            except ImportError:
                pass

        # Universal fallback
        try:
            from plyer import notification

            return "plyer"
        except ImportError:
            return "console"  # Always fallback to console

    def _is_in_cooldown(self) -> bool:
        """Check if in cooldown period."""
        if not self._last_notification_time:
            return False
        return datetime.now() - self._last_notification_time < timedelta(seconds=self.config.cooldown_seconds)

    def _send_notification(self, title: str, message: str) -> bool:
        """Send notification using the detected method."""
        try:
            if self._working_method == "osascript":
                # Most reliable method on macOS
                script = f'display notification "{message}" with title "{title}"'
                result = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5, text=True)
                return result.returncode == 0

            elif self._working_method == "pync":
                try:
                    import pync

                    pync.notify(message, title=title, timeout=self.config.duration_seconds)
                    return True
                except Exception:
                    # If pync fails, fall back to osascript
                    script = f'display notification "{message}" with title "{title}"'
                    result = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
                    return result.returncode == 0

            elif self._working_method == "notify-send":
                result = subprocess.run(
                    ["notify-send", "--expire-time", str(self.config.duration_seconds * 1000), title, message],
                    capture_output=True,
                    timeout=5,
                )
                return result.returncode == 0

            elif self._working_method == "win10toast":
                from win10toast import ToastNotifier

                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=self.config.duration_seconds, threaded=True)
                return True

            elif self._working_method == "plyer":
                from plyer import notification

                notification.notify(title=title, message=message, timeout=self.config.duration_seconds)
                return True

            else:  # console fallback
                print(f"\n🔔 {title}")
                print(f"💬 {message}")
                return True

        except Exception as e:
            # Always fall back to console if anything fails
            print(f"\n🔔 {title}")
            print(f"💬 {message}")
            print(f"(Notification error: {e})")
            return True

    def show_mindful_moment(self) -> bool:
        """Show mindful moment notification if not in cooldown."""
        if not self.config.enabled:
            return False

        if self._is_in_cooldown():
            return False

        success = self._send_notification(self.config.title, self.config.message)

        if success:
            self._last_notification_time = datetime.now()

        return success

    def test_notification(self) -> bool:
        """Test notification system."""
        return self._send_notification("Mindful Touch Test", "🎉 This is a test notification!")

    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown seconds."""
        if not self._is_in_cooldown():
            return 0.0
        elapsed = datetime.now() - self._last_notification_time
        return max(0.0, self.config.cooldown_seconds - elapsed.total_seconds())
