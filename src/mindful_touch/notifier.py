"""
Cross-platform notification system for Mindful Touch.

This module provides gentle, non-intrusive desktop notifications with
intelligent cooldown management and platform-specific optimizations.
"""

import platform
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from .config import NotificationConfig


class NotificationProvider(ABC):
    """Abstract base class for platform-specific notification providers."""

    @abstractmethod
    def show_notification(self, title: str, message: str, duration: int = 3) -> bool:
        """Show a desktop notification.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds

        Returns:
            True if notification was successfully displayed
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this notification provider is available on the system."""
        pass


class WindowsNotificationProvider(NotificationProvider):
    """Windows notification provider using win10toast."""

    def __init__(self):
        self._toaster = None
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Windows notifications are available."""
        if platform.system() != "Windows":
            return False

        try:
            from win10toast import ToastNotifier

            self._toaster = ToastNotifier()
            return True
        except ImportError:
            # Fallback to plyer if win10toast is not available
            try:
                from plyer import notification

                return True
            except ImportError:
                return False

    @property
    def is_available(self) -> bool:
        return self._available

    def show_notification(self, title: str, message: str, duration: int = 3) -> bool:
        """Show Windows toast notification.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds

        Returns:
            True if notification was shown successfully
        """
        if not self.is_available:
            return False

        try:
            if self._toaster:
                # Use win10toast for better Windows integration
                self._toaster.show_toast(
                    title=title, msg=message, duration=duration, threaded=True
                )
            else:
                # Fallback to plyer
                from plyer import notification

                notification.notify(title=title, message=message, timeout=duration)
            return True
        except Exception as e:
            print(f"⚠️  Windows notification failed: {e}")
            return False


class MacOSNotificationProvider(NotificationProvider):
    """macOS notification provider using osascript."""

    def __init__(self):
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if macOS notifications are available."""
        if platform.system() != "Darwin":
            return False

        try:
            # Test if osascript is available
            result = subprocess.run(
                ["which", "osascript"], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def show_notification(self, title: str, message: str, duration: int = 3) -> bool:
        """Show macOS notification using osascript.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds (macOS handles timing automatically)

        Returns:
            True if notification was shown successfully
        """
        if not self.is_available:
            return False

        try:
            # Create AppleScript command for notification
            script = f"""
                display notification "{message}" with title "{title}" sound name "Glass"
            """

            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=5
            )

            return result.returncode == 0
        except Exception as e:
            print(f"⚠️  macOS notification failed: {e}")
            return False


class LinuxNotificationProvider(NotificationProvider):
    """Linux notification provider using notify-send."""

    def __init__(self):
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if Linux notifications are available."""
        if platform.system() != "Linux":
            return False

        try:
            # Test if notify-send is available
            result = subprocess.run(
                ["which", "notify-send"], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            # Fallback to plyer
            try:
                from plyer import notification

                return True
            except ImportError:
                return False

    @property
    def is_available(self) -> bool:
        return self._available

    def show_notification(self, title: str, message: str, duration: int = 3) -> bool:
        """Show Linux notification using notify-send.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds

        Returns:
            True if notification was shown successfully
        """
        if not self.is_available:
            return False

        try:
            # Try notify-send first
            duration_ms = duration * 1000
            result = subprocess.run(
                [
                    "notify-send",
                    "--urgency=low",
                    "--expire-time",
                    str(duration_ms),
                    "--icon=dialog-information",
                    title,
                    message,
                ],
                capture_output=True,
                timeout=5,
            )

            if result.returncode == 0:
                return True

        except Exception as e:
            print(f"⚠️  notify-send failed: {e}")

        # Fallback to plyer
        try:
            from plyer import notification

            notification.notify(title=title, message=message, timeout=duration)
            return True
        except Exception as e:
            print(f"⚠️  Linux notification fallback failed: {e}")
            return False


class FallbackNotificationProvider(NotificationProvider):
    """Fallback notification provider using plyer for maximum compatibility."""

    def __init__(self):
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if plyer is available."""
        try:
            from plyer import notification

            return True
        except ImportError:
            return False

    @property
    def is_available(self) -> bool:
        return self._available

    def show_notification(self, title: str, message: str, duration: int = 3) -> bool:
        """Show notification using plyer.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds

        Returns:
            True if notification was shown successfully
        """
        if not self.is_available:
            return False

        try:
            from plyer import notification

            notification.notify(title=title, message=message, timeout=duration)
            return True
        except Exception as e:
            print(f"⚠️  Fallback notification failed: {e}")
            return False


class ConsoleNotificationProvider(NotificationProvider):
    """Console-only notification provider for headless or unsupported systems."""

    @property
    def is_available(self) -> bool:
        return True  # Always available as last resort

    def show_notification(self, title: str, message: str, duration: int = 3) -> bool:
        """Show notification in console.

        Args:
            title: Notification title
            message: Notification message
            duration: Duration in seconds (ignored for console)

        Returns:
            Always True
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🔔 [{timestamp}] {title}: {message}")
        return True


class NotificationManager:
    """Manages desktop notifications with intelligent cooldown and platform detection."""

    def __init__(self, config: NotificationConfig):
        """Initialize notification manager.

        Args:
            config: Notification configuration
        """
        self.config = config
        self._last_notification_time: Optional[datetime] = None
        self._provider = self._get_best_provider()

        print(f"📱 Using notification provider: {type(self._provider).__name__}")

    def _get_best_provider(self) -> NotificationProvider:
        """Get the best available notification provider for the current platform.

        Returns:
            Best available notification provider
        """
        providers = [
            WindowsNotificationProvider(),
            MacOSNotificationProvider(),
            LinuxNotificationProvider(),
            FallbackNotificationProvider(),
            ConsoleNotificationProvider(),  # Always works as last resort
        ]

        for provider in providers:
            if provider.is_available:
                return provider

        # This should never happen since ConsoleNotificationProvider is always available
        return ConsoleNotificationProvider()

    def _is_in_cooldown(self) -> bool:
        """Check if we're still in the cooldown period.

        Returns:
            True if in cooldown period
        """
        if self._last_notification_time is None:
            return False

        cooldown_period = timedelta(seconds=self.config.cooldown_seconds)
        return datetime.now() - self._last_notification_time < cooldown_period

    def show_mindful_moment(self, custom_message: Optional[str] = None) -> bool:
        """Show a mindful moment notification.

        Args:
            custom_message: Optional custom message to override config

        Returns:
            True if notification was shown
        """
        if not self.config.enabled:
            return False

        if self._is_in_cooldown():
            return False

        message = custom_message or self.config.message
        success = self._provider.show_notification(
            title=self.config.title,
            message=message,
            duration=self.config.duration_seconds,
        )

        if success:
            self._last_notification_time = datetime.now()

        return success

    def show_custom_notification(
        self, title: str, message: str, bypass_cooldown: bool = False
    ) -> bool:
        """Show a custom notification.

        Args:
            title: Notification title
            message: Notification message
            bypass_cooldown: Whether to bypass cooldown period

        Returns:
            True if notification was shown
        """
        if not self.config.enabled:
            return False

        if not bypass_cooldown and self._is_in_cooldown():
            return False

        success = self._provider.show_notification(
            title=title, message=message, duration=self.config.duration_seconds
        )

        if success and not bypass_cooldown:
            self._last_notification_time = datetime.now()

        return success

    def test_notification(self) -> bool:
        """Test the notification system.

        Returns:
            True if test notification was shown successfully
        """
        return self.show_custom_notification(
            title="Mindful Touch Test",
            message="Notification system is working! 🎉",
            bypass_cooldown=True,
        )

    def update_config(self, config: NotificationConfig) -> None:
        """Update notification configuration.

        Args:
            config: New notification configuration
        """
        self.config = config

    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds.

        Returns:
            Remaining cooldown time in seconds (0 if not in cooldown)
        """
        if not self._is_in_cooldown():
            return 0.0

        elapsed = datetime.now() - self._last_notification_time
        remaining = self.config.cooldown_seconds - elapsed.total_seconds()
        return max(0.0, remaining)

    @property
    def provider_name(self) -> str:
        """Get the name of the current notification provider.

        Returns:
            Name of the current notification provider
        """
        return type(self._provider).__name__.replace("NotificationProvider", "")


def create_notification_manager(config: NotificationConfig) -> NotificationManager:
    """Create a notification manager with the given configuration.

    Args:
        config: Notification configuration

    Returns:
        Configured notification manager
    """
    return NotificationManager(config)
