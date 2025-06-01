"""Cross-platform notification system."""

import platform
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from .config import NotificationConfig


class NotificationManager:
    """Manages desktop notifications with cooldown."""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self._last_notification_time: Optional[datetime] = None
        self.system = platform.system()

    def _is_in_cooldown(self) -> bool:
        """Check if in cooldown period."""
        if not self._last_notification_time:
            return False
        return datetime.now() - self._last_notification_time < timedelta(seconds=self.config.cooldown_seconds)

    def _show_notification(self, title: str, message: str) -> bool:
        """Platform-specific notification display."""
        try:
            if self.system == "Darwin":  # macOS
                script = f'display notification "{message}" with title "{title}" sound name "Glass"'
                subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
                return True

            elif self.system == "Linux":
                subprocess.run(
                    [
                        "notify-send",
                        "--urgency=low",
                        "--expire-time",
                        str(self.config.duration_seconds * 1000),
                        title,
                        message,
                    ],
                    capture_output=True,
                    timeout=5,
                )
                return True

            elif self.system == "Windows":
                try:
                    from win10toast import ToastNotifier

                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=self.config.duration_seconds, threaded=True)
                    return True
                except ImportError:
                    pass

            # Fallback to plyer
            try:
                from plyer import notification

                notification.notify(title=title, message=message, timeout=self.config.duration_seconds)
                return True
            except Exception:
                pass

            # Last resort: console
            print(f"\n🔔 {title}: {message}")
            return True

        except Exception as e:
            print(f"Notification error: {e}")
            return False

    def show_mindful_moment(self) -> bool:
        """Show mindful moment notification if not in cooldown."""
        if not self.config.enabled or self._is_in_cooldown():
            return False

        success = self._show_notification(self.config.title, self.config.message)
        if success:
            self._last_notification_time = datetime.now()
        return success

    def test_notification(self) -> bool:
        """Test notification system."""
        return self._show_notification("Mindful Touch Test", "Notifications working! 🎉")

    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown seconds."""
        if not self._is_in_cooldown():
            return 0.0
        elapsed = datetime.now() - self._last_notification_time
        return max(0.0, self.config.cooldown_seconds - elapsed.total_seconds())
