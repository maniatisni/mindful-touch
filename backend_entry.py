#!/usr/bin/env python3
"""
Standalone entry point for Mindful Touch backend
This file is used by PyInstaller to create a standalone executable
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main function
if __name__ == "__main__":
    from backend.detection.main import main

    main()
