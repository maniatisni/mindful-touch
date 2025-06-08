#!/usr/bin/env python3
"""Nuitka build script for Mindful Touch."""

import os
import sys
import subprocess
import shutil


def find_mediapipe_path():
    """Find MediaPipe installation path."""
    try:
        import mediapipe

        return mediapipe.__path__[0]
    except ImportError:
        print("❌ MediaPipe not found in current environment")
        sys.exit(1)


def clean_build():
    """Clean previous builds."""
    for name in ["gui_main.app", "gui_main.dist", "gui_main.build"]:
        if os.path.exists(name):
            print(f"🧹 Cleaning {name}")
            shutil.rmtree(name)


def build_with_nuitka():
    """Build using Nuitka with all necessary data files."""
    print("🔨 Building Mindful Touch with Nuitka...")

    # Find MediaPipe path
    mediapipe_path = find_mediapipe_path()
    print(f"📦 Found MediaPipe at: {mediapipe_path}")

    # Clean previous builds
    clean_build()

    # Build command
    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--macos-create-app-bundle",
        "--macos-app-icon=logo.icns",
        # Include project data
        "--include-data-dir=config=config",
        # Include MediaPipe data files - THIS IS THE KEY FIX
        f"--include-data-dir={mediapipe_path}/modules=mediapipe/modules",
        f"--include-data-dir={mediapipe_path}/python=mediapipe/python",
        # Include any other MediaPipe directories that exist
        # Check for common MediaPipe data directories
        *(
            [f"--include-data-dir={mediapipe_path}/framework=mediapipe/framework"]
            if os.path.exists(f"{mediapipe_path}/framework")
            else []
        ),
        *(
            [f"--include-data-dir={mediapipe_path}/tasks=mediapipe/tasks"]
            if os.path.exists(f"{mediapipe_path}/tasks")
            else []
        ),
        # Qt plugin
        "--enable-plugin=pyside6",
        "--disable-console",
        # App metadata
        "--macos-app-name=Mindful Touch",
        "--company-name=Mindful Touch",
        "--product-name=Mindful Touch",
        "--file-version=1.0.0",
        "--product-version=1.0.0",
        # Source file
        "src/mindful_touch/gui_main.py",
    ]

    print("🚀 Running Nuitka...")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        print(f"📱 App created: gui_main.app")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        print(f"Error output:\n{e.stderr}")
        if e.stdout:
            print(f"Standard output:\n{e.stdout}")
        return False


def verify_mediapipe_files():
    """Verify that MediaPipe files are included in the app bundle."""
    app_path = "gui_main.app"
    if not os.path.exists(app_path):
        print("❌ App bundle not found")
        return False

    # Check for MediaPipe modules
    mediapipe_modules = os.path.join(app_path, "Contents", "MacOS", "mediapipe", "modules")
    if os.path.exists(mediapipe_modules):
        print(f"✅ MediaPipe modules found at: {mediapipe_modules}")

        # List some key files
        face_landmark_file = os.path.join(mediapipe_modules, "face_landmark", "face_landmark_front_cpu.binarypb")
        if os.path.exists(face_landmark_file):
            print("✅ Face landmark model found")
        else:
            print("❌ Face landmark model missing")
            return False

        hand_landmark_dir = os.path.join(mediapipe_modules, "hand_landmark")
        if os.path.exists(hand_landmark_dir):
            print("✅ Hand landmark models directory found")
        else:
            print("⚠️  Hand landmark models directory not found")

        return True
    else:
        print(f"❌ MediaPipe modules not found at: {mediapipe_modules}")
        return False


def main():
    """Main build function."""
    print("🚀 Mindful Touch - Nuitka Build")
    print("=" * 40)

    # Build the app
    if build_with_nuitka():
        print("\n🔍 Verifying MediaPipe files...")
        if verify_mediapipe_files():
            print("\n✅ Build successful! MediaPipe files are included.")
            print("🎉 You can now run: open gui_main.app")
        else:
            print("\n⚠️  Build completed but MediaPipe files may be missing.")
            print("The app might still have the missing model file error.")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
