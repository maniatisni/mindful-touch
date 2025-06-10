#!/usr/bin/env python3
"""
Build script for creating Mindful Touch macOS application using PyInstaller with UV
"""

import os
import shutil
import subprocess
import sys

# Build configuration
APP_NAME = "Mindful Touch"
APP_VERSION = "0.1.0"
BUNDLE_ID = "com.mindfultouch.app"


def check_uv_env():
    """Check if we're running in a uv environment"""
    venv_path = os.environ.get("VIRTUAL_ENV")
    if not venv_path:
        print("❌ Not running in a virtual environment. Please run with 'uv run python build_macos.py'")
        sys.exit(1)
    print(f"✅ Using virtual environment: {venv_path}")


def create_spec_file():
    """Create PyInstaller spec file with proper configuration"""

    # Get Python version for site-packages path
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(os.path.abspath(SPECPATH)).parent

block_cipher = None

# Collect all necessary data files
datas = [
    (str('logo.png'), '.'),
    (str('logo.icns'), '.'),
    # Add any other data files here
]

# Add MediaPipe data files
import site
mediapipe_path = None

# Try to find mediapipe in the virtual environment
venv_path = os.environ.get('VIRTUAL_ENV')
if venv_path:
    possible_path = os.path.join(venv_path, 'lib', 'python{python_version}', 'site-packages', 'mediapipe')
    if os.path.exists(possible_path):
        mediapipe_path = possible_path
        print(f"Found mediapipe at: {{mediapipe_path}}")
        datas.append((mediapipe_path, 'mediapipe'))

# Add pync terminal-notifier binary
pync_path = None
if venv_path:
    possible_pync = os.path.join(venv_path, 'lib', 'python{python_version}', 'site-packages', 'pync')
    if os.path.exists(possible_pync):
        pync_path = possible_pync
        print(f"Found pync at: {{pync_path}}")
        datas.append((pync_path, 'pync'))

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'mindful_touch',
    'mindful_touch.config',
    'mindful_touch.detector',
    'mindful_touch.notifier',
    'mindful_touch.main',
    'mindful_touch.ui',
    'mindful_touch.ui.qt_gui',
    'mindful_touch.ui.detection_worker',
    'mindful_touch.ui.status_widget',
    'mindful_touch.ui.settings_widget',
    'pydantic',
    'pydantic.dataclasses',
    'pydantic._internal',
    'pydantic._internal._core_utils',
    'platformdirs',
    'plyer',
    'plyer.platforms.macosx',
    'plyer.platforms.macosx.notification',
    'pync',
    'pync.TerminalNotifier',
    'cv2',
    'mediapipe',
    'mediapipe.python',
    'mediapipe.python.solutions',
    'mediapipe.python.solutions.face_mesh',
    'mediapipe.python.solutions.hands',
    'numpy',
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'click',
    'click.core',
    'click.decorators',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_agg',
    'google.protobuf',
    'google.protobuf.pyext._message',
]

# Binaries to include (like terminal-notifier for pync)
binaries = []

# Analysis configuration
a = Analysis(
    ['src/mindful_touch/__main__.py'],
    pathex=[
        'src',
        str(project_root / 'src'),
        str(project_root / '.venv' / 'lib' / 'python{python_version}' / 'site-packages'),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.',],  # Look for hooks in current directory
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'ipykernel',
        'pytest',
        'ruff',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mindful-touch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='entitlements.plist',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='mindful-touch',
)

app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon=str('logo.icns'),
    bundle_identifier='{BUNDLE_ID}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': '{APP_NAME}',
        'CFBundleGetInfoString': "Mindful Touch - Trichotillomania Detection",
        'CFBundleIdentifier': '{BUNDLE_ID}',
        'CFBundleVersion': '{APP_VERSION}',
        'CFBundleShortVersionString': '{APP_VERSION}',
        'NSHighResolutionCapable': True,
        'NSCameraUsageDescription': 'Mindful Touch needs camera access to detect hand movements.',
        'NSAppleEventsUsageDescription': 'Mindful Touch needs to display notifications.',
        'LSMinimumSystemVersion': '10.13.0',
        'LSApplicationCategoryType': 'public.app-category.healthcare-fitness',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    }},
)
"""

    with open("mindful-touch.spec", "w") as f:
        f.write(spec_content)

    print("✅ Created mindful-touch.spec")


def create_entitlements():
    """Create entitlements.plist for macOS permissions"""

    entitlements_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Camera access -->
    <key>com.apple.security.device.camera</key>
    <true/>
    <!-- Allow sending Apple events (for notifications via osascript) -->
    <key>com.apple.security.automation.apple-events</key>
    <true/>

    <!-- File access for config storage -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <!-- Network client (might be needed for some dependencies) -->
    <key>com.apple.security.network.client</key>
    <true/>
    <!-- Hardened runtime -->
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <!-- Allow DYLD environment variables (needed for some Python packages) -->
    <key>com.apple.security.cs.allow-dyld-environment-variables</key>
    <true/>
    <!-- Disable library validation (needed for loading Python extensions) -->
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>"""

    with open("entitlements.plist", "w") as f:
        f.write(entitlements_content)

    print("✅ Created entitlements.plist")


def create_icon():
    """Ensure icon files exist"""
    if not os.path.exists("logo.icns"):
        print("⚠️  Warning: logo.icns not found.")
        if os.path.exists("logo.png"):
            print("   Creating logo.icns from logo.png...")
            try:
                subprocess.run(["sips", "-s", "format", "icns", "logo.png", "--out", "logo.icns"], check=True)
                print("✅ Created logo.icns")
            except Exception as e:
                print(f"❌ Failed to create logo.icns: {e}. Please create it manually.")
        else:
            print("   Please add your icon files (logo.png and logo.icns)")
            return False

    if not os.path.exists("logo.png"):
        print("⚠️  Warning: logo.png not found. Please add your logo file.")
        return False

    return True


def create_hooks():
    """Create PyInstaller hooks for problematic packages"""

    # Create hook for pync
    pync_hook = """# hook-pync.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# Collect everything from pync
datas, binaries, hiddenimports = collect_all('pync')

# Ensure terminal-notifier binary is included    import os
    try:
        import pync
        pync_path = os.path.dirname(pync.__file__)
        # Look for terminal-notifier in various possible locations
        possible_paths = [
            os.path.join(pync_path, 'vendor', 'terminal-notifier-2.0.0', 'terminal-notifier.app'),
            os.path.join(pync_path, 'vendor', 'terminal-notifier', 'terminal-notifier.app'),
            os.path.join(pync_path, 'terminal-notifier.app'),
        ]
        for path in possible_paths:
        if os.path.exists(path):
            # Add the entire .app bundle
            datas.append((path, os.path.join('pync', 'vendor', os.path.basename(os.path.dirname(path)))))
            break
except Exception as e:
    print(f"Warning in pync hook: {e}")
"""

    with open("hook-pync.py", "w") as f:
        f.write(pync_hook)

    # Create hook for mediapipe
    mediapipe_hook = """# hook-mediapipe.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files from mediapipe
datas = collect_data_files('mediapipe', include_py_files=True)

# Collect all submodules
hiddenimports = collect_submodules('mediapipe')

# Add protobuf imports
hiddenimports += [
    'google.protobuf.pyext._message',
    'google.protobuf.internal.builder',
    'google.protobuf.internal.containers',
]
"""

    with open("hook-mediapipe.py", "w") as f:
        f.write(mediapipe_hook)

    print("✅ Created PyInstaller hooks")


def install_dependencies():
    """Install PyInstaller and other build dependencies using uv"""
    print("📦 Installing build dependencies...")

    # First, let's make sure all project dependencies are installed
    print("   Installing project dependencies...")
    subprocess.run(["uv", "sync"], check=True)

    # Install PyInstaller
    print("   Installing PyInstaller...")
    subprocess.run(["uv", "pip", "install", "pyinstaller>=6.0"], check=True)

    # Install additional dependencies that might be needed
    print("   Installing additional dependencies...")
    subprocess.run(["uv", "pip", "install", "pillow", "matplotlib"], check=True)

    # Reinstall pync to ensure it's properly installed
    print("   Reinstalling pync...")
    subprocess.run(["uv", "pip", "uninstall", "-y", "pync"], check=False)
    subprocess.run(["uv", "pip", "install", "pync"], check=True)


def build_app():
    """Build the application"""
    print("🔨 Building application...")

    # Create necessary files
    create_spec_file()
    create_entitlements()
    create_hooks()

    if not create_icon():
        print("⚠️  Continuing without icons...")

    # Clean previous builds
    if os.path.exists("dist"):
        print("🧹 Cleaning previous build...")
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")

    # Run PyInstaller with uv's Python
    print("🏗️  Running PyInstaller...")
    result = subprocess.run(["pyinstaller", "--clean", "--noconfirm", "mindful-touch.spec"])

    if result.returncode == 0:
        print("✅ Build successful!")
        print(f"📁 Application created at: dist/{APP_NAME}.app")

        # Create DMG installer (optional)
        if shutil.which("create-dmg"):
            create_dmg()
        else:
            print("\n💡 To create a DMG installer, install create-dmg:")
            print("   brew install create-dmg")
    else:
        print("❌ Build failed!")
        sys.exit(1)


def create_dmg():
    """Create a DMG installer"""
    print("\n📀 Creating DMG installer...")

    dmg_name = f"{APP_NAME}-{APP_VERSION}.dmg"

    # Remove old DMG if exists
    if os.path.exists(dmg_name):
        os.remove(dmg_name)

    try:
        subprocess.run(
            [
                "create-dmg",
                "--volname",
                APP_NAME,
                "--volicon",
                "logo.icns",
                "--window-pos",
                "200",
                "120",
                "--window-size",
                "800",
                "400",
                "--icon-size",
                "100",
                "--icon",
                f"{APP_NAME}.app",
                "200",
                "190",
                "--hide-extension",
                f"{APP_NAME}.app",
                "--app-drop-link",
                "600",
                "185",
                "--no-internet-enable",  # For compatibility
                dmg_name,
                f"dist/{APP_NAME}.app",
            ],
            check=True,
        )

        print(f"✅ DMG created: {dmg_name}")
    except subprocess.CalledProcessError:
        print("❌ DMG creation failed. The .app bundle is still available in the dist/ folder.")


def post_build_fixes():
    """Apply any necessary post-build fixes"""
    app_path = f"dist/{APP_NAME}.app"

    if not os.path.exists(app_path):
        print("❌ App bundle not found, skipping post-build fixes")
        return

    # Fix file permissions
    print("🔧 Fixing permissions...")
    subprocess.run(["chmod", "-R", "755", app_path])

    # Copy logo files to Resources folder as backup
    resources_path = f"{app_path}/Contents/Resources"
    for logo_file in ["logo.png", "logo.icns"]:
        if os.path.exists(logo_file):
            dest = os.path.join(resources_path, logo_file)
            if not os.path.exists(dest):
                shutil.copy2(logo_file, resources_path)

    # Manual fix for pync if needed
    print("🔧 Checking pync installation...")
    pync_check_script = f"""#!/bin/bash
# Check if pync's terminal-notifier is in the app
find "{app_path}" -name "terminal-notifier*" -type f 2>/dev/null | head -5
"""

    with open("check_pync.sh", "w") as f:
        f.write(pync_check_script)
    os.chmod("check_pync.sh", 0o755)

    # Create a simple test script
    test_script = f"""#!/bin/bash
echo "Testing {APP_NAME}..."
open "{app_path}"
echo "Check Console.app for any error messages"
"""

    with open("test_app.sh", "w") as f:
        f.write(test_script)
    os.chmod("test_app.sh", 0o755)

    print("✅ Applied post-build fixes")
    print("💡 Run ./test_app.sh to test the application")
    print("💡 Run ./check_pync.sh to verify pync files")


if __name__ == "__main__":
    print("🌸 Mindful Touch macOS App Builder")
    print(f"   Version: {APP_VERSION}")
    print()

    # Check environment
    check_uv_env()

    # Check if we're in the right directory
    if not os.path.exists("pyproject.toml"):
        print("❌ Error: Run this script from the project root directory")
        sys.exit(1)

    try:
        install_dependencies()
        build_app()
        post_build_fixes()

        print("\n🎉 Build complete!")
        print("\n📋 Next steps:")
        print("1. Test the app: ./test_app.sh")
        print("2. Or directly: open 'dist/Mindful Touch.app'")
        print("3. Share the .app with users (they may need to right-click → Open on first run)")
        print("4. For wider distribution, consider code signing")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
