#!/usr/bin/env python3
"""
Standalone entry point for Mindful Touch backend
This file is used by PyInstaller to create a standalone executable
"""

import os
import sys
from pathlib import Path

# Set matplotlib environment BEFORE any imports for fastest startup
os.environ.setdefault("MPLBACKEND", "Agg")

# Disable matplotlib font caching completely - we don't need fonts for MediaPipe
import types
import sys

# Create a dummy matplotlib module to bypass font loading
class DummyMatplotlib:
    def __init__(self):
        self.font_manager = types.SimpleNamespace()
        self.pyplot = types.SimpleNamespace()
        
    def __getattr__(self, name):
        return types.SimpleNamespace()

# Pre-install dummy matplotlib before MediaPipe imports it
sys.modules['matplotlib'] = DummyMatplotlib()
sys.modules['matplotlib.pyplot'] = types.SimpleNamespace()
sys.modules['matplotlib.font_manager'] = types.SimpleNamespace()

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main function
if __name__ == "__main__":
    from backend.detection.main import main

    main()
