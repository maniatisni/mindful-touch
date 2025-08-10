# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(SPEC))
sys.path.insert(0, project_root)

a = Analysis(
    ['mindful_touch_gui.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        # Include GUI resources if any
        ('backend/gui/styles', 'backend/gui/styles'),
        ('backend/gui/resources', 'backend/gui/resources'),
    ],
    hiddenimports=[
        'backend.gui.main_window',
        'backend.gui.widgets.custom_toggle',
        'backend.gui.widgets.camera_display',
        'backend.gui.widgets.detection_worker',
        'backend.audio.sound_manager',
        'backend.detection.multi_region_detector',
        'mediapipe',
        'cv2',
        'numpy',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib.tests',
        'numpy.tests',
        'PIL.Tests'
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mindful-touch-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mindful-touch-gui',
)

app = BUNDLE(
    coll,
    name='Mindful Touch.app',
    icon=None,  # Add icon path if available
    bundle_identifier='com.mindfultouch.app',
    info_plist={
        'CFBundleName': 'Mindful Touch',
        'CFBundleDisplayName': 'Mindful Touch',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSCameraUsageDescription': 'Mindful Touch uses the camera to detect hand movements for mindfulness awareness.',
        'NSMicrophoneUsageDescription': 'Mindful Touch does not use the microphone.',
        'NSHumanReadableCopyright': 'Copyright © 2025 Mindful Touch. All rights reserved.',
        'CFBundleDocumentTypes': [],
        'LSMinimumSystemVersion': '10.15.0',
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
    },
)