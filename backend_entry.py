#!/usr/bin/env python3
"""
Standalone entry point for Mindful Touch backend
This file is used by PyInstaller to create a standalone executable
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the main function
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mindful Touch Backend Entry Point")
    parser.add_argument("--build", action="store_true", help="Build the backend executable")
    args = parser.parse_args()

    if args.build:
        import PyInstaller.__main__
        import shutil

        # Define paths
        work_path = "build"
        dist_path = "dist"
        executable_name = "mindful-touch-backend"

        # Run PyInstaller
        PyInstaller.__main__.run([
            __file__,
            "--name=%s" % executable_name,
            "--onefile",
            "--windowed",
            "--distpath=%s" % dist_path,
            "--workpath=%s" % work_path,
            "--specpath=%s" % work_path,
        ])

        # Move the executable to the correct location for Tauri
        os.makedirs("frontend/src-tauri/bin", exist_ok=True)
        shutil.move(
            os.path.join(dist_path, executable_name),
            os.path.join("frontend/src-tauri/bin", executable_name),
        )
    else:
        from backend.detection.main import main
        main()