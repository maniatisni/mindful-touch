"""Entry point for mindful_touch package"""

import sys

from mindful_touch.main import main

if __name__ == "__main__":
    # Check if we're running from an app bundle
    if sys.platform == "darwin" and ".app/Contents/MacOS" in sys.executable:
        # Force GUI mode when running as a macOS app
        sys.argv = [sys.argv[0], "gui"]

    sys.exit(main())
