#!/usr/bin/env python3
"""
Standalone entry point for Mindful Touch backend
This file is used by PyInstaller to create a standalone executable
"""

import sys
import types

# Completely stub matplotlib before any imports
class DummyMatplotlib:
    def __init__(self):
        pass
    def __getattr__(self, name):
        return DummyMatplotlib()
    def __call__(self, *args, **kwargs):
        return DummyMatplotlib()

# Install dummy matplotlib modules
sys.modules['matplotlib'] = DummyMatplotlib()
sys.modules['matplotlib.pyplot'] = DummyMatplotlib()
sys.modules['matplotlib.font_manager'] = DummyMatplotlib()
sys.modules['matplotlib.backends'] = DummyMatplotlib()
sys.modules['matplotlib.backends.backend_agg'] = DummyMatplotlib()

import backend.bootstrap_mpl
from backend.detection.main import main

if __name__ == "__main__":
    main()
