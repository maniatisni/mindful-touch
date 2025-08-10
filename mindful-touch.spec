# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Add current directory to Python path
spec_path = Path(SPECPATH)
sys.path.insert(0, str(spec_path))

a = Analysis(
    ['main.py'],
    pathex=[str(spec_path)],
    binaries=[],
    datas=[
        # Include system sounds for alerts
        ('/System/Library/Sounds/Glass.aiff', 'sounds'),
        # Include MediaPipe model files
        ('.venv/lib/python3.9/site-packages/mediapipe/modules', 'mediapipe/modules'),
        ('.venv/lib/python3.9/site-packages/mediapipe/python/solutions', 'mediapipe/python/solutions'),
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        # MediaPipe dependencies
        'mediapipe',
        'cv2',
        'numpy',
        # Backend modules
        'backend.detection.multi_region_detector',
        'backend.detection.config',
        # UI modules  
        'ui.status_overlay',
        'ui.settings_panel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Only exclude modules we're sure we don't need
        'IPython',
        'jupyter',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Mindful Touch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

app = BUNDLE(
    exe,
    name='Mindful Touch.app',
    icon=None,
    bundle_identifier='com.mindfultouch.app',
    info_plist={
        'CFBundleName': 'Mindful Touch',
        'CFBundleDisplayName': 'Mindful Touch',
        'CFBundleIdentifier': 'com.mindfultouch.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'NSCameraUsageDescription': 'Mindful Touch uses the camera to detect hand movements near your face for mindfulness awareness.',
        'NSPrincipalClass': 'NSApplication',
        'LSUIElement': False,  # Show in dock
    },
)