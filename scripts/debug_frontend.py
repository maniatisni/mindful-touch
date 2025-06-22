#!/usr/bin/env python3
"""
Debug script to help troubleshoot frontend-backend integration
"""
import subprocess
import sys
import time
import asyncio
import json
import websockets
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_websocket_manually():
    """Test if we can connect to WebSocket manually"""
    print("🔗 Testing manual WebSocket connection...")
    
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("✅ WebSocket connection successful!")
            
            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent ping")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"📥 Received: {data}")
            
            if data.get("type") == "pong":
                print("✅ Ping-pong successful - backend is working!")
            elif data.get("type") == "detection_data":
                print("✅ Received detection data - backend is streaming!")
            
            return True
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_python_backend():
    """Test starting the Python backend manually"""
    print("🐍 Testing Python backend startup...")
    
    try:
        # Test if we can run the backend command
        result = subprocess.run(
            ["uv", "run", "python", "-m", "backend.detection.main", "--help"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Python backend command works")
            return True
        else:
            print(f"❌ Python backend command failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test Python backend: {e}")
        return False

def check_paths():
    """Check if the paths that Tauri might use exist"""
    print("📁 Checking paths that Tauri might use...")
    
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    # Simulate being in different Tauri locations
    possible_tauri_locations = [
        current_dir / "frontend" / "src-tauri",
        current_dir / "frontend" / "src-tauri" / "target" / "debug",
    ]
    
    for tauri_location in possible_tauri_locations:
        print(f"\n📍 Simulating Tauri running from: {tauri_location}")
        
        # Check different relative paths from this location
        test_paths = [
            "../../",
            "../../../", 
            "../../../../",
            "./"
        ]
        
        for rel_path in test_paths:
            try:
                abs_path = (tauri_location / rel_path).resolve()
                pyproject_path = abs_path / "pyproject.toml"
                backend_path = abs_path / "backend" / "detection" / "main.py"
                
                pyproject_exists = pyproject_path.exists()
                backend_exists = backend_path.exists()
                
                status = "✅" if (pyproject_exists and backend_exists) else "❌"
                print(f"  {status} {rel_path} -> {abs_path}")
                print(f"      pyproject.toml: {'✅' if pyproject_exists else '❌'}")
                print(f"      backend/detection/main.py: {'✅' if backend_exists else '❌'}")
                
                if pyproject_exists and backend_exists:
                    print(f"      🎯 This path should work!")
                    
            except Exception as e:
                print(f"  ❌ {rel_path} -> Error: {e}")

async def main():
    """Main debug function"""
    print("🔍 Frontend-Backend Integration Debug Tool")
    print("=" * 60)
    
    # Test 1: Check paths
    check_paths()
    
    print("\n" + "=" * 60)
    
    # Test 2: Test Python backend command
    backend_works = test_python_backend()
    
    print("\n" + "=" * 60)
    
    # Test 3: Test WebSocket connection (if backend is already running)
    ws_works = await test_websocket_manually()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    
    if not backend_works:
        print("❌ Python backend command doesn't work - check your UV installation")
        print("   Try: uv --version")
        print("   Try: cd to project root and run: uv run python -m backend.detection.main --help")
    
    if not ws_works:
        print("❌ WebSocket connection failed - backend might not be running")
        print("   Try starting backend manually: uv run python -m backend.detection.main --headless")
        print("   Then test the frontend again")
    
    if backend_works and not ws_works:
        print("🚀 SOLUTION: Start the backend manually first, then try the frontend:")
        print("   1. In terminal 1: uv run python -m backend.detection.main --headless")
        print("   2. In terminal 2: cd frontend && cargo tauri dev")
        print("   3. In the app, press 'Start Detection' (it should connect to the already-running backend)")

if __name__ == "__main__":
    asyncio.run(main())