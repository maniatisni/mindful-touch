#!/usr/bin/env python3
"""
Test script to verify mock camera functionality for CI environments
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import cv2
import websockets

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_mock_camera_backend():
    """Test the backend with mock camera"""
    print("🎭 Testing mock camera backend...")

    # Start backend with mock camera
    process = subprocess.Popen(
        [sys.executable, "-m", "backend.detection.main", "--headless", "--mock-camera"],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Give backend time to start
        print("⏳ Waiting for backend to initialize...")
        await asyncio.sleep(5)

        # Test WebSocket connection
        print("🔗 Testing WebSocket connection...")
        uri = "ws://localhost:8765"

        async with websockets.connect(uri) as websocket:
            print("✅ Successfully connected to WebSocket")

            # Test ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent ping")

            # Wait for response
            for _attempt in range(10):
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)

                if data["type"] == "pong":
                    print("✅ Received pong response")
                    break
                elif data["type"] == "detection_data":
                    print(f"📊 Received detection data: {data['data']}")
                    # Check if mock data looks reasonable
                    required_fields = ["hands_detected", "face_detected", "contact_points", "alerts_active"]
                    if all(field in data["data"] for field in required_fields):
                        print("✅ Mock detection data has correct structure")
                    break

            print("🎉 Mock camera backend test completed successfully!")

    finally:
        # Cleanup
        print("🧹 Cleaning up backend process...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def test_mock_camera_direct():
    """Test the mock camera directly"""
    print("🎭 Testing MockCamera directly...")

    from backend.detection.camera_utils import MockCamera

    # Create mock camera
    camera = MockCamera(640, 480)
    print(f"✅ Created MockCamera: {camera.width}x{camera.height}")

    # Test basic properties
    assert camera.isOpened()
    assert camera.get(cv2.CAP_PROP_FRAME_WIDTH) == 640
    assert camera.get(cv2.CAP_PROP_FRAME_HEIGHT) == 480
    print("✅ Mock camera properties work correctly")

    # Test frame generation
    for i in range(5):
        ret, frame = camera.read()
        assert ret
        assert frame.shape == (480, 640, 3)
        print(f"✅ Frame {i + 1}: {frame.shape}, type: {frame.dtype}")

    camera.release()
    print("✅ Mock camera direct test completed successfully!")


def main():
    """Main test runner"""
    print("🚀 Mock Camera Test Suite")
    print("=" * 50)

    # Test 1: Direct mock camera test
    try:
        test_mock_camera_direct()
    except Exception as e:
        print(f"❌ Direct mock camera test failed: {e}")
        return 1

    print("\n" + "=" * 50)

    # Test 2: Backend integration test
    try:
        asyncio.run(test_mock_camera_backend())
    except Exception as e:
        print(f"❌ Backend integration test failed: {e}")
        return 1

    print("\n🎉 All mock camera tests passed!")
    print("✅ Ready for CI/CD deployment!")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
