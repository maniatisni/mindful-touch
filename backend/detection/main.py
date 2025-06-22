"""
Mindful Touch - Multi-Region Detection
Gentle awareness tool for mindful hand movement tracking
"""

import sys
import argparse
import cv2

from .config import Config
from .multi_region_detector import MultiRegionDetector
from .camera_utils import initialize_camera


def main():
    parser = argparse.ArgumentParser(description="Mindful Touch - Multi-Region Detection")
    parser.add_argument("--headless", action="store_true", help="Run without GUI (for Tauri)")
    parser.add_argument("--camera", type=int, help="Camera index to use")
    args = parser.parse_args()

    print("Mindful Touch - Multi-Region Detection")
    print(f"Mode: {'Headless' if args.headless else 'GUI'}")
    print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")

    # Initialize multi-region detector
    detector = MultiRegionDetector()

    # Initialize camera with dynamic detection
    cap = initialize_camera(
        camera_index=args.camera,
        width=Config.CAMERA_WIDTH,
        height=Config.CAMERA_HEIGHT
    )

    if cap is None:
        print("Error: Could not open any camera")
        return

    if args.headless:
        run_headless_mode(cap, detector)
    else:
        run_gui_mode(cap, detector)


def run_headless_mode(cap, detector):
    """Run detection without GUI - WebSocket mode for Tauri"""
    import json
    import time
    import asyncio
    import logging
    from ..server import DetectionWebSocketServer
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("Running in headless mode with WebSocket server...")
    print("WebSocket server will be available at ws://localhost:8765")
    
    # Create and start WebSocket server
    ws_server = DetectionWebSocketServer()
    server_thread = ws_server.run_in_thread()
    
    # Give server time to start
    time.sleep(1)
    
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Process frame (without visualization)
            _, detection_data = detector.process_frame(frame)

            # Check for region toggle requests from WebSocket (simplified)
            # Note: For now we'll keep the region toggles simple
            # In the future we could use proper async handling
            
            # Send detection data via WebSocket every 3 frames
            frame_count += 1
            if frame_count % 3 == 0:
                detection_output = {
                    "timestamp": time.time(),
                    "active_regions": Config.ACTIVE_REGIONS,
                    **detection_data
                }
                ws_server.update_detection_data(detection_output)

            # Small delay to prevent overwhelming the system
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("Detection service interrupted")
    finally:
        cap.release()
        detector.cleanup()
        print("Detection service stopped")


def run_gui_mode(cap, detector):
    """Run detection with GUI"""
    print("Camera initialized. Controls:")
    print("  'q' = quit")
    print("  's' = toggle scalp")
    print("  'e' = toggle eyebrows")
    print("  'y' = toggle eyes")
    print("  'm' = toggle mouth")
    print("  'b' = toggle beard")

    # Main loop
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Process frame
            annotated_frame, detection_data = detector.process_frame(frame)

            # Add status overlay
            _draw_status_overlay(annotated_frame, detection_data)

            # Display frame
            cv2.imshow("Mindful Touch - Multi-Region Detection", annotated_frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                detector.toggle_region("scalp")
                print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")
            elif key == ord("e"):
                detector.toggle_region("eyebrows")
                print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")
            elif key == ord("y"):
                detector.toggle_region("eyes")
                print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")
            elif key == ord("m"):
                detector.toggle_region("mouth")
                print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")
            elif key == ord("b"):
                detector.toggle_region("beard")
                print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        detector.cleanup()
        print("Cleanup complete.")


def _draw_status_overlay(frame, detection_data):
    """Draw status information overlay for multi-region detection"""
    height, width = frame.shape[:2]

    # Status background
    overlay = frame.copy()
    cv2.rectangle(overlay, (width - 280, 10), (width - 10, 180), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Status text
    y_offset = 35
    line_height = 20

    # Detection status
    hands_status = "✓" if detection_data["hands_detected"] else "✗"
    face_status = "✓" if detection_data["face_detected"] else "✗"

    cv2.putText(
        frame,
        f"Hands: {hands_status}",
        (width - 270, y_offset),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0) if detection_data["hands_detected"] else (0, 0, 255),
        1,
    )

    cv2.putText(
        frame,
        f"Face: {face_status}",
        (width - 270, y_offset + line_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0) if detection_data["face_detected"] else (0, 0, 255),
        1,
    )

    # Active regions
    active_regions = ", ".join(Config.ACTIVE_REGIONS) if Config.ACTIVE_REGIONS else "None"
    cv2.putText(frame, f"Active: {active_regions[:20]}", (width - 270, y_offset + 2 * line_height), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

    # Contact points
    contact_color = (0, 0, 255) if detection_data["contact_points"] > 0 else (255, 255, 255)
    cv2.putText(
        frame,
        f"Contacts: {detection_data['contact_points']}",
        (width - 270, y_offset + 3 * line_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        contact_color,
        1,
    )

    # Alert status
    alerts = ", ".join(detection_data["alerts_active"]) if detection_data["alerts_active"] else "None"
    alert_color = (0, 0, 255) if detection_data["alerts_active"] else (255, 255, 255)
    cv2.putText(frame, f"Alerts: {alerts[:15]}", (width - 270, y_offset + 4 * line_height), cv2.FONT_HERSHEY_SIMPLEX, 0.5, alert_color, 1)

    # Controls reminder
    cv2.putText(frame, "s/e/y/m/b = toggle regions", (width - 270, y_offset + 6 * line_height), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (128, 128, 128), 1)


if __name__ == "__main__":
    main()
