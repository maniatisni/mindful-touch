#!/usr/bin/env python3
"""Main entry point for Mindful Touch PyQt GUI."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.gui.main_window import main

if __name__ == "__main__":
    sys.exit(main())