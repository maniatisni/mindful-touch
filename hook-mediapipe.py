# hook-mediapipe.py
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
