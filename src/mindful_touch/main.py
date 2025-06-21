"""
Mindful Touch - Multi-Region Detection
Gentle awareness tool for mindful hand movement tracking
"""


import cv2

from .config import Config
from .multi_region_detector import MultiRegionDetector


def main():
    print("Mindful Touch - Multi-Region Detection")
    print(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")

    # Initialize multi-region detector
    detector = MultiRegionDetector()

    # Initialize camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)

    if not cap.isOpened():
        print("Error: Could not open camera")
        return

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
