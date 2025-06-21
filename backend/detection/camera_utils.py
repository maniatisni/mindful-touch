"""
Camera utilities for dynamic camera detection
"""
import cv2


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
                
                available_cameras.append({
                    'index': i,
                    'width': int(width),
                    'height': int(height),
                    'fps': int(fps) if fps > 0 else 30
                })
            cap.release()
    
    return available_cameras


def get_best_camera_index():
    """Get the best available camera (highest resolution preference)"""
    cameras = find_available_cameras()
    
    if not cameras:
        print("No cameras found!")
        return None
    
    # Prefer external cameras (usually higher index) with better resolution
    best_camera = max(cameras, key=lambda x: (x['width'] * x['height'], x['index']))
    
    print(f"Selected camera {best_camera['index']}: {best_camera['width']}x{best_camera['height']}")
    return best_camera['index']


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