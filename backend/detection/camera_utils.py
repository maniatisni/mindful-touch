"""
Camera utilities for dynamic camera detection
"""

import cv2
import numpy as np


class MockCamera:
    """Mock camera for CI/testing environments without hardware camera"""

    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.frame_count = 0
        print(f"MockCamera initialized: {width}x{height}")

    def read(self):
        """Generate a mock frame with some dynamic content"""
        # Create a simple gradient background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Add gradient
        for y in range(self.height):
            frame[y, :, 0] = int(50 + (y / self.height) * 100)  # Blue gradient
            frame[y, :, 1] = int(30 + (y / self.height) * 80)  # Green gradient
            frame[y, :, 2] = int(20 + (y / self.height) * 60)  # Red gradient

        # Add some dynamic moving elements to simulate hand/face detection areas
        self.frame_count += 1

        # Simulate face area (upper center)
        face_x = self.width // 2 + int(50 * np.sin(self.frame_count * 0.1))
        face_y = self.height // 3
        cv2.circle(frame, (face_x, face_y), 80, (100, 150, 200), -1)

        # Simulate hands (moving)
        hand1_x = self.width // 3 + int(30 * np.cos(self.frame_count * 0.08))
        hand1_y = self.height // 2 + int(20 * np.sin(self.frame_count * 0.12))
        cv2.circle(frame, (hand1_x, hand1_y), 40, (150, 100, 100), -1)

        hand2_x = 2 * self.width // 3 + int(25 * np.sin(self.frame_count * 0.09))
        hand2_y = self.height // 2 + int(30 * np.cos(self.frame_count * 0.11))
        cv2.circle(frame, (hand2_x, hand2_y), 35, (150, 100, 100), -1)

        return True, frame

    def release(self):
        """Mock release method"""
        print("MockCamera released")

    def isOpened(self):
        """Mock isOpened method"""
        return True

    def get(self, prop):
        """Mock get method for camera properties"""
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            return self.width
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.height
        elif prop == cv2.CAP_PROP_FPS:
            return 30
        return 0

    def set(self, prop, value):
        """Mock set method for camera properties"""
        if prop == cv2.CAP_PROP_FRAME_WIDTH:
            self.width = int(value)
        elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
            self.height = int(value)
        return True


def find_available_cameras(max_index=10):
    """Find all available camera indices"""
    available_cameras = []

    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # Test if we can actually read a frame
            ret, _ = cap.read()
            if ret:
                # Get camera info
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                fps = cap.get(cv2.CAP_PROP_FPS)

                available_cameras.append({"index": i, "width": int(width), "height": int(height), "fps": int(fps) if fps > 0 else 30})
            cap.release()

    return available_cameras


def get_best_camera_index():
    """Get the best available camera (highest resolution preference)"""
    cameras = find_available_cameras()

    if not cameras:
        print("No cameras found!")
        return None

    # Prefer external cameras (usually higher index) with better resolution
    best_camera = max(cameras, key=lambda x: (x["width"] * x["height"], x["index"]))

    print(f"Selected camera {best_camera['index']}: {best_camera['width']}x{best_camera['height']}")
    return best_camera["index"]


def initialize_camera(camera_index=None, width=1280, height=720):
    """Initialize camera with given or auto-detected index"""
    if camera_index is None:
        camera_index = get_best_camera_index()
        if camera_index is None:
            return None

    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return None

    return cap
