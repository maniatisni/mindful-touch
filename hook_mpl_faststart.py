"""
PyInstaller runtime hook for matplotlib fast startup
Optimizes matplotlib font cache handling to eliminate 30+ second startup delays
"""
import os
import pathlib
import sys

def setup_matplotlib_cache():
    """Set up matplotlib configuration for fast startup"""
    try:
        # Always use headless backend for performance
        os.environ.setdefault("MPLBACKEND", "Agg")
        
        # Try to use bundled cache first
        bundled_cache = pathlib.Path(sys._MEIPASS) / "mplcache" if hasattr(sys, '_MEIPASS') else None
        
        if bundled_cache and bundled_cache.exists():
            # Use the bundled pre-built cache
            os.environ.setdefault("MPLCONFIGDIR", str(bundled_cache))
            print(f"[FontCache] Using bundled cache: {bundled_cache}")
        else:
            # Fallback to persistent user cache
            if sys.platform == "darwin":  # macOS
                cache_base = pathlib.Path.home() / "Library" / "Caches" / "mindful-touch"
            elif sys.platform == "win32":  # Windows
                cache_base = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "mindful-touch"
            else:  # Linux
                cache_base = pathlib.Path.home() / ".cache" / "mindful-touch"
            
            mpl_cache_dir = cache_base / "matplotlib"
            mpl_cache_dir.mkdir(parents=True, exist_ok=True)
            
            os.environ.setdefault("MPLCONFIGDIR", str(mpl_cache_dir))
            print(f"[FontCache] Using user cache: {mpl_cache_dir}")
        
    except Exception as e:
        print(f"[FontCache] Warning: Could not set up matplotlib cache: {e}")
        # Fallback to headless mode only
        os.environ.setdefault("MPLBACKEND", "Agg")

# Execute setup immediately when hook runs
setup_matplotlib_cache()