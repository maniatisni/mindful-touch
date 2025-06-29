# PyInstaller spec file for Mindful Touch backend
# This creates a standalone executable that includes all Python dependencies

import sys
import os
from pathlib import Path

# Add the project root to the path  
project_root = Path('.').resolve()
sys.path.insert(0, str(project_root))

# Find the actual virtual environment path
venv_path = None
for possible_venv in ['.venv', 'venv', '.virtualenv']:
    if (project_root / possible_venv).exists():
        venv_path = project_root / possible_venv
        break

# MediaPipe data files (auto-detected)
datas = []
try:
    import mediapipe
    mp_path = Path(mediapipe.__file__).parent
    # Include MediaPipe modules and data
    datas.extend([
        (str(mp_path / 'modules'), 'mediapipe/modules'),
        (str(mp_path / 'python'), 'mediapipe/python'),
    ])
    print(f"MediaPipe found at: {mp_path}")
except ImportError:
    print("Warning: MediaPipe not found, proceeding without data files")

a = Analysis(
    ['backend_entry.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'mediapipe',
        'mediapipe.python.solutions',
        'mediapipe.python.solutions.face_mesh',
        'mediapipe.python.solutions.hands',
        'cv2',
        'numpy',
        'websockets',
        'asyncio',
        'backend.detection.multi_region_detector',
        'backend.server.websocket_server',
        'backend.detection.config',
        'backend.detection.camera_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'pytest',
        'test',
        'tests',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mindful-touch-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)