# hook-pync.py
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# Collect everything from pync
datas, binaries, hiddenimports = collect_all('pync')

# Ensure terminal-notifier binary is included - with improved path handling
import os
import sys
import glob
try:
    import pync
    pync_path = os.path.dirname(pync.__file__)
    print(f"Found pync at: {pync_path}")
    
    # Look for terminal-notifier in various possible locations
    possible_paths = [
        os.path.join(pync_path, 'vendor', 'terminal-notifier-2.0.0', 'terminal-notifier.app'),
        os.path.join(pync_path, 'vendor', 'terminal-notifier', 'terminal-notifier.app'),
        os.path.join(pync_path, 'terminal-notifier.app'),
    ]
    
    # Also try to find it using glob pattern
    vendor_dir = os.path.join(pync_path, 'vendor')
    if os.path.exists(vendor_dir):
        glob_matches = glob.glob(os.path.join(vendor_dir, '**', 'terminal-notifier.app'), recursive=True)
        possible_paths.extend(glob_matches)
    
    found = False
    for path in possible_paths:
        if os.path.exists(path):
            # Add the entire .app bundle with a simplified destination path
            dest_dir = 'pync/vendor'
            print(f"Adding terminal-notifier from: {path} to {dest_dir}")
            datas.append((path, dest_dir))
            found = True
            break
    
    if not found:
        print("WARNING: Could not find terminal-notifier.app bundle for pync")
except Exception as e:
    print(f"Warning in pync hook: {e}")
