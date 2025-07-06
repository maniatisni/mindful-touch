#!/usr/bin/env python3
"""
Pre-build matplotlib font cache for faster startup
Run this during CI/build process to generate fontlist cache
"""
import os
import sys
import pathlib
import tempfile
import shutil

def prebuild_cache():
    """Pre-build matplotlib font cache"""
    print("[FontCache] Pre-building matplotlib font cache...")
    
    # Create temporary cache directory
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = pathlib.Path(temp_dir) / "mplcache"
        cache_dir.mkdir(exist_ok=True)
        
        # Set environment variables
        os.environ["MPLBACKEND"] = "Agg"
        os.environ["MPLCONFIGDIR"] = str(cache_dir)
        
        try:
            # Import matplotlib to trigger font cache building
            import matplotlib
            import matplotlib.pyplot as plt
            
            # Create a simple figure to ensure cache is built
            plt.figure(figsize=(1, 1))
            plt.close('all')
            
            print(f"[FontCache] Cache built in: {cache_dir}")
            
            # Copy to project build directory
            build_cache = pathlib.Path("build/mplcache")
            if build_cache.exists():
                shutil.rmtree(build_cache)
            
            build_cache.parent.mkdir(exist_ok=True)
            shutil.copytree(cache_dir, build_cache)
            print(f"[FontCache] Cache copied to: {build_cache}")
            
            # List cache contents
            print("[FontCache] Cache contents:")
            for item in build_cache.rglob("*"):
                if item.is_file():
                    print(f"  {item.relative_to(build_cache)} ({item.stat().st_size} bytes)")
            
        except Exception as e:
            print(f"[FontCache] Error building cache: {e}")
            sys.exit(1)
    
    print("[FontCache] Pre-build complete!")

if __name__ == "__main__":
    prebuild_cache()