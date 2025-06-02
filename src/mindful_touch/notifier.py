"""Cross-platform notification system with comprehensive debugging."""

import os
import platform
import subprocess
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from .config import NotificationConfig


class NotificationManager:
    """Manages desktop notifications with comprehensive debugging and fallbacks."""

    def __init__(self, config: NotificationConfig):
        self.config = config
        self._last_notification_time: Optional[datetime] = None
        self.system = platform.system()
        self._debug_info: List[str] = []
        self._working_method: Optional[str] = None

        print(f"🔍 Initializing notifications on {self.system}...")
        self._run_comprehensive_diagnostics()

    def _add_debug(self, message: str) -> None:
        """Add debug information."""
        self._debug_info.append(message)
        print(f"🐛 {message}")

    def _run_comprehensive_diagnostics(self) -> None:
        """Run comprehensive notification diagnostics."""
        print("\n" + "=" * 60)
        print("🩺 NOTIFICATION SYSTEM DIAGNOSTICS")
        print("=" * 60)

        # System info
        self._add_debug(f"Operating System: {self.system}")
        self._add_debug(f"Platform: {platform.platform()}")
        self._add_debug(f"Python: {sys.version}")

        if self.system == "Darwin":
            self._diagnose_macos()
        elif self.system == "Linux":
            self._diagnose_linux()
        elif self.system == "Windows":
            self._diagnose_windows()

        self._test_all_methods()
        print("=" * 60 + "\n")

    def _diagnose_macos(self) -> None:
        """Comprehensive macOS notification diagnostics."""
        self._add_debug("🍎 Running macOS diagnostics...")

        # Check macOS version
        try:
            result = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self._add_debug(f"macOS Version: {version}")
            else:
                self._add_debug("❌ Could not determine macOS version")
        except Exception as e:
            self._add_debug(f"❌ Error checking macOS version: {e}")

        # Check if running in terminal that has notification permissions
        terminal_app = os.environ.get("TERM_PROGRAM", "Unknown")
        self._add_debug(f"Terminal Program: {terminal_app}")

        # Check Focus/Do Not Disturb status
        try:
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to return (do not disturb of dock preferences)',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                dnd_status = result.stdout.strip()
                self._add_debug(f"Do Not Disturb: {dnd_status}")
                if dnd_status.lower() == "true":
                    self._add_debug("⚠️ Do Not Disturb is ENABLED - this blocks notifications!")
            else:
                self._add_debug("Could not check Do Not Disturb status")
        except Exception as e:
            self._add_debug(f"Error checking Do Not Disturb: {e}")

        # Check if terminal-notifier is available
        try:
            result = subprocess.run(["which", "terminal-notifier"], capture_output=True, text=True)
            if result.returncode == 0:
                self._add_debug(f"terminal-notifier found at: {result.stdout.strip()}")
            else:
                self._add_debug("❌ terminal-notifier not found")
        except Exception:
            self._add_debug("❌ Could not check for terminal-notifier")

        # Check pync availability
        try:
            import pync

            self._add_debug("✅ pync module available")
            # Try to get terminal-notifier version
            try:
                result = subprocess.run(["terminal-notifier", "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    self._add_debug(f"terminal-notifier version: {result.stdout.strip()}")
            except Exception:
                pass
        except ImportError:
            self._add_debug("❌ pync module not installed")

        print("\n📋 macOS Notification Troubleshooting Guide:")
        print("1. System Settings > Notifications & Focus")
        print("   - Find your terminal app (Terminal, iTerm2, VS Code, etc.)")
        print("   - Enable 'Allow Notifications'")
        print("   - Set alert style to 'Banners' or 'Alerts'")
        print("2. Check for 'terminal-notifier' in the notification list")
        print("3. Turn OFF 'Do Not Disturb' and 'Focus' modes")
        print("4. If using external monitor, enable 'Allow notifications when mirroring'")
        print("5. Install pync: pip install pync")

    def _diagnose_linux(self) -> None:
        """Comprehensive Linux notification diagnostics."""
        self._add_debug("🐧 Running Linux diagnostics...")

        # Check desktop environment
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown")
        self._add_debug(f"Desktop Environment: {desktop}")

        display = os.environ.get("DISPLAY", "Not set")
        self._add_debug(f"DISPLAY variable: {display}")

        # Check if notify-send is available
        try:
            result = subprocess.run(["which", "notify-send"], capture_output=True, text=True)
            if result.returncode == 0:
                self._add_debug(f"notify-send found at: {result.stdout.strip()}")
            else:
                self._add_debug("❌ notify-send not found")
        except Exception:
            self._add_debug("❌ Could not check for notify-send")

        # Check notification daemon
        try:
            result = subprocess.run(["pgrep", "-f", "notification"], capture_output=True, text=True)
            if result.returncode == 0:
                self._add_debug("✅ Notification daemon appears to be running")
            else:
                self._add_debug("❌ No notification daemon found")
        except Exception:
            self._add_debug("Could not check notification daemon")

        print("\n📋 Linux Notification Troubleshooting Guide:")
        print("1. Install notify-send: sudo apt install libnotify-bin")
        print("2. Check if notification daemon is running: pgrep -f notification")
        print("3. Test manually: notify-send 'Test' 'This is a test'")
        print("4. Install plyer: pip install plyer")

    def _diagnose_windows(self) -> None:
        """Windows notification diagnostics."""
        self._add_debug("🪟 Running Windows diagnostics...")

        try:
            import win10toast

            self._add_debug("✅ win10toast available")
        except ImportError:
            self._add_debug("❌ win10toast not installed")

        print("\n📋 Windows Notification Troubleshooting Guide:")
        print("1. Install win10toast: pip install win10toast")
        print("2. Check Windows notification settings")

    def _test_all_methods(self) -> None:
        """Test all available notification methods."""
        self._add_debug("🧪 Testing notification methods...")

        methods_to_test = []
        if self.system == "Darwin":
            methods_to_test = [
                ("pync", self._test_pync),
                ("osascript", self._test_osascript),
                ("plyer", self._test_plyer),
            ]
        elif self.system == "Linux":
            methods_to_test = [("notify-send", self._test_notify_send), ("plyer", self._test_plyer)]
        elif self.system == "Windows":
            methods_to_test = [("win10toast", self._test_win10toast), ("plyer", self._test_plyer)]

        for method_name, test_func in methods_to_test:
            try:
                if test_func():
                    self._add_debug(f"✅ {method_name} test PASSED")
                    if not self._working_method:
                        self._working_method = method_name
                else:
                    self._add_debug(f"❌ {method_name} test FAILED")
            except Exception as e:
                self._add_debug(f"❌ {method_name} test ERROR: {e}")

        if self._working_method:
            self._add_debug(f"🎯 Will use method: {self._working_method}")
        else:
            self._add_debug("❌ No working notification methods found!")

    def _test_pync(self) -> bool:
        """Test pync notifications."""
        try:
            import pync

            result = pync.notify("Debug Test", title="pync Test", timeout=1)
            return True
        except Exception as e:
            self._add_debug(f"pync error: {e}")
            return False

    def _test_osascript(self) -> bool:
        """Test osascript notifications."""
        try:
            script = 'display notification "Debug Test" with title "osascript Test"'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            self._add_debug(f"osascript error: {e}")
            return False

    def _test_notify_send(self) -> bool:
        """Test notify-send."""
        try:
            result = subprocess.run(
                ["notify-send", "--expire-time=1000", "notify-send Test", "Debug Test"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception as e:
            self._add_debug(f"notify-send error: {e}")
            return False

    def _test_win10toast(self) -> bool:
        """Test win10toast."""
        try:
            from win10toast import ToastNotifier

            toaster = ToastNotifier()
            toaster.show_toast("win10toast Test", "Debug Test", duration=1, threaded=True)
            return True
        except Exception as e:
            self._add_debug(f"win10toast error: {e}")
            return False

    def _test_plyer(self) -> bool:
        """Test plyer notifications."""
        try:
            from plyer import notification

            notification.notify(title="plyer Test", message="Debug Test", timeout=1)
            return True
        except Exception as e:
            self._add_debug(f"plyer error: {e}")
            return False

    def _is_in_cooldown(self) -> bool:
        """Check if in cooldown period."""
        if not self._last_notification_time:
            return False
        return datetime.now() - self._last_notification_time < timedelta(seconds=self.config.cooldown_seconds)

    def _show_notification(self, title: str, message: str) -> bool:
        """Show notification using the working method."""
        if not self._working_method:
            print(f"\n🔔 CONSOLE NOTIFICATION: {title}")
            print(f"💬 {message}")
            return True

        success = False
        try:
            if self._working_method == "pync":
                import pync

                pync.notify(message, title=title, sound="Glass", timeout=self.config.duration_seconds)
                success = True
            elif self._working_method == "osascript":
                script = f'display notification "{message}" with title "{title}" sound name "Glass"'
                result = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
                success = result.returncode == 0
            elif self._working_method == "notify-send":
                result = subprocess.run(
                    [
                        "notify-send",
                        "--urgency=normal",
                        "--expire-time",
                        str(self.config.duration_seconds * 1000),
                        "--icon=dialog-information",
                        title,
                        message,
                    ],
                    capture_output=True,
                    timeout=5,
                )
                success = result.returncode == 0
            elif self._working_method == "win10toast":
                from win10toast import ToastNotifier

                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=self.config.duration_seconds, threaded=True)
                success = True
            elif self._working_method == "plyer":
                from plyer import notification

                notification.notify(title=title, message=message, timeout=self.config.duration_seconds)
                success = True
        except Exception as e:
            print(f"❌ Notification failed with {self._working_method}: {e}")
            success = False

        if not success:
            print(f"\n🔔 FALLBACK NOTIFICATION: {title}")
            print(f"💬 {message}")
            success = True

        return success

    def show_mindful_moment(self) -> bool:
        """Show mindful moment notification if not in cooldown."""
        if not self.config.enabled:
            print("🔇 Notifications disabled in config")
            return False

        if self._is_in_cooldown():
            remaining = self.get_cooldown_remaining()
            print(f"🔇 In cooldown: {remaining:.1f}s remaining")
            return False

        print(f"🔔 Attempting to show notification using: {self._working_method or 'console'}")
        success = self._show_notification(self.config.title, self.config.message)

        if success:
            self._last_notification_time = datetime.now()
            print("✅ Notification sent successfully!")
        else:
            print("❌ Notification failed!")

        return success

    def test_notification(self) -> bool:
        """Test notification system with detailed feedback."""
        print("\n🧪 Testing notification system...")
        print(f"Method: {self._working_method or 'None found'}")

        success = self._show_notification("Mindful Touch Test", "🎉 This is a test notification!")

        if success:
            print("✅ Test notification sent!")
            print("\n👀 Check your screen for the notification popup")
            if self.system == "Darwin":
                print("💡 If you don't see it, check the troubleshooting steps above")
        else:
            print("❌ Test notification failed!")

        return success

    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown seconds."""
        if not self._is_in_cooldown():
            return 0.0
        elapsed = datetime.now() - self._last_notification_time
        return max(0.0, self.config.cooldown_seconds - elapsed.total_seconds())

    def print_debug_info(self) -> None:
        """Print all collected debug information."""
        print("\n📊 DEBUG SUMMARY:")
        for info in self._debug_info:
            print(f"  {info}")
