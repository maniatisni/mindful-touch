# -*- mode: python ; coding: utf-8 -*-

import glob
import sys
from pathlib import Path

block_cipher = None

# Add current directory to Python path
spec_path = Path(SPECPATH)
sys.path.insert(0, str(spec_path))

# Locate MediaPipe in the venv regardless of Python minor version
mediapipe_matches = glob.glob(str(spec_path / '.venv/lib/python3.*/site-packages/mediapipe'))
if not mediapipe_matches:
    raise SystemExit('Could not find mediapipe in .venv — run `uv sync` first')
mediapipe_site = mediapipe_matches[0]

datas = [
    # Include MediaPipe model files
    (f'{mediapipe_site}/modules', 'mediapipe/modules'),
    (f'{mediapipe_site}/python/solutions', 'mediapipe/python/solutions'),
    # Bundled Work Sans fonts + logo
    ('assets/fonts', 'assets/fonts'),
    ('assets/logo.svg', 'assets'),
]

a = Analysis(
    ['main.py'],
    pathex=[str(spec_path)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        # MediaPipe dependencies
        'mediapipe',
        'cv2',
        'numpy',
        # Backend modules
        'backend.detection.multi_region_detector',
        'backend.detection.config',
        'backend.detection.settings_store',
        # UI modules
        'ui.panels.camera_panel',
        'ui.panels.detection_panel',
        'ui.styles.theme',
        'ui.widgets.status_badge',
        'ui.widgets.toggle_switch',
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
    icon='logo.icns',
)

app = BUNDLE(
    exe,
    name='Mindful Touch.app',
    icon='logo.icns',
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
