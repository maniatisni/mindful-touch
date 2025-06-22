"""
Mindful Touch - Multi-Region Detection
Gentle awareness tool for mindful hand movement tracking
"""

import argparse
import base64
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import cv2

from .camera_utils import MockCamera, initialize_camera
from .config import Config
from .multi_region_detector import MultiRegionDetector


def main():
    parser = argparse.ArgumentParser(description="Mindful Touch - Multi-Region Detection")
    parser.add_argument("--headless", action="store_true", help="Run without GUI (for Tauri)")
    parser.add_argument("--camera", type=int, help="Camera index to use")
    parser.add_argument("--mock-camera", action="store_true", help="Use mock camera for CI/testing")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Configure logging level
    import logging

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    if args.verbose:
        logger.info("Mindful Touch - Multi-Region Detection")
        logger.info(f"Mode: {'Headless' if args.headless else 'GUI'}")
        logger.info(f"Active regions: {', '.join(Config.ACTIVE_REGIONS)}")

        # Print paths to help debug import issues in production
        import os
        import sys

        logger.debug(f"Python executable: {sys.executable}")
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Python path: {sys.path}")

    # Initialize multi-region detector
    if args.verbose:
        logger.info("Initializing detector...")
    detector = MultiRegionDetector()

    # Initialize camera with dynamic detection or mock for CI
    if args.mock_camera:
        if args.verbose:
            logger.info("Using mock camera for CI/testing environment")
        cap = MockCamera(Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)
    else:
        if args.verbose:
            logger.info("Initializing camera...")
        cap = initialize_camera(camera_index=args.camera, width=Config.CAMERA_WIDTH, height=Config.CAMERA_HEIGHT)

        if cap is None:
            if args.verbose:
                logger.warning("Could not open any camera, falling back to mock camera")
            cap = MockCamera(Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)

    if args.headless:
        run_headless_mode(cap, detector, verbose=args.verbose)
    else:
        run_gui_mode(cap, detector)


def run_headless_mode(cap, detector, verbose=False):
    """Run detection without GUI - WebSocket mode for Tauri with threading"""
    import logging
    import os

    from ..server import DetectionWebSocketServer

    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # Print additional debug info
    if verbose:
        logger.debug(f"Current working directory: {os.getcwd()}")
        logger.debug(f"Process ID: {os.getpid()}")
        import platform

        logger.debug(f"Platform: {platform.platform()}")
        logger.debug(f"Python version: {platform.python_version()}")

    if verbose:
        logger.info("Running in headless mode with WebSocket server and threading...")
        logger.info("WebSocket server will be available at ws://localhost:8765")

    # Create and start WebSocket server
    port = 8765
    max_port_attempts = 5
    ws_server = None

    for attempt in range(max_port_attempts):
        try:
            logger.info(f"Attempting to start WebSocket server on port {port} (attempt {attempt + 1}/{max_port_attempts})")
            ws_server = DetectionWebSocketServer(port=port)
            ws_server.run_in_thread()
            logger.info(f"WebSocket server started on port {port}")
            break
        except Exception as e:
            logger.warning(f"Failed to start WebSocket server on port {port}: {e}")
            port += 1

    if ws_server is None:
        logger.error(f"Failed to start WebSocket server after {max_port_attempts} attempts")
        return

    # Threading setup
    frame_queue = queue.Queue(maxsize=2)  # Small queue to prevent lag
    shutdown_event = threading.Event()

    # Create thread pool for frame processing (increased for high quality)
    executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="frame_processor")

    def camera_capture_thread():
        """Dedicated thread for camera capture"""
        frame_count = 0
        while not shutdown_event.is_set():
            try:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Could not read frame from camera")
                    break

                frame = cv2.flip(frame, 1)  # Mirror effect
                frame_count += 1

                # Put frame in queue, drop old frames if queue full
                try:
                    frame_queue.put_nowait((frame_count, frame))
                except queue.Full:
                    # Drop oldest frame to prevent lag
                    try:
                        frame_queue.get_nowait()
                        frame_queue.put_nowait((frame_count, frame))
                    except queue.Empty:
                        pass

            except Exception as e:
                logger.error(f"Camera capture error: {e}")
                break

    def frame_processing_thread():
        """Dedicated thread for detection processing and encoding"""
        while not shutdown_event.is_set():
            try:
                frame_count, frame = frame_queue.get(timeout=0.1)

                # Process detection in parallel
                future_detection = executor.submit(detector.process_frame, frame)

                # Check for region toggles
                toggle_request = ws_server.get_region_toggle_sync()
                if toggle_request:
                    region = toggle_request.get("region")
                    enabled = toggle_request.get("enabled")
                    if enabled:
                        if region not in Config.ACTIVE_REGIONS:
                            Config.ACTIVE_REGIONS.append(region)
                            logger.info(f"Region '{region}' enabled")
                    else:
                        if region in Config.ACTIVE_REGIONS:
                            Config.ACTIVE_REGIONS.remove(region)
                            logger.info(f"Region '{region}' disabled")

                # Get detection results
                _, detection_data = future_detection.result()

                # Send to WebSocket if clients connected
                if len(ws_server.clients) > 0:
                    # Encode frame asynchronously
                    future_encoding = executor.submit(encode_frame_for_streaming, frame)

                    # Send detection data immediately
                    detection_output = {
                        "timestamp": time.time(),
                        "active_regions": Config.ACTIVE_REGIONS,
                        **detection_data,
                    }

                    # Send every 2nd frame for good performance
                    if frame_count % 2 == 0:
                        try:
                            frame_base64 = future_encoding.result(timeout=0.1)  # Shorter timeout for better responsiveness
                            detection_output["frame"] = frame_base64
                        except Exception:
                            pass  # Skip frame if encoding takes too long

                    ws_server.update_detection_data(detection_output)

                if verbose and frame_count % 60 == 0:
                    logger.debug(f"Frame {frame_count}: {len(ws_server.clients)} clients, {detection_data.get('contact_points', 0)} contacts")

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Frame processing error: {e}")

    # Start threads
    camera_thread = threading.Thread(target=camera_capture_thread, name="camera_capture")
    processing_thread = threading.Thread(target=frame_processing_thread, name="frame_processing")

    camera_thread.start()
    processing_thread.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(0.1)
            if not camera_thread.is_alive() or not processing_thread.is_alive():
                break
    except KeyboardInterrupt:
        logger.info("Detection service interrupted by keyboard")
    finally:
        # Cleanup
        shutdown_event.set()
        camera_thread.join(timeout=2.0)
        processing_thread.join(timeout=2.0)
        executor.shutdown(wait=True)
        cap.release()
        detector.cleanup()
        logger.info("Detection service stopped and resources released")


def encode_frame_for_streaming(frame):
    """Encode frame for streaming - optimized for speed with good quality"""
    height, width = frame.shape[:2]

    # Use good resolution for balance of quality and speed
    new_width = min(width, 960)  # Slightly smaller for better performance
    new_height = int(height * (new_width / width))

    # Use linear interpolation for good quality and speed
    resized_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    # Use high quality JPEG (skip PNG for speed)
    encode_params_jpg = [
        cv2.IMWRITE_JPEG_QUALITY,
        85,  # Good quality, much faster than 98%
        cv2.IMWRITE_JPEG_OPTIMIZE,
        1,  # Keep optimization for size
    ]
    _, buffer = cv2.imencode(".jpg", resized_frame, encode_params_jpg)
    return base64.b64encode(buffer).decode("utf-8")


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
    cv2.putText(
        frame,
        f"Active: {active_regions[:20]}",
        (width - 270, y_offset + 2 * line_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (0, 255, 255),
        1,
    )

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
    cv2.putText(
        frame,
        f"Alerts: {alerts[:15]}",
        (width - 270, y_offset + 4 * line_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        alert_color,
        1,
    )

    # Controls reminder
    cv2.putText(
        frame,
        "s/e/y/m/b = toggle regions",
        (width - 270, y_offset + 6 * line_height),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (128, 128, 128),
        1,
    )


if __name__ == "__main__":
    main()
