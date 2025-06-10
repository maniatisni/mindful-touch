"""Trichotillomania-specific detection using MediaPipe."""

import math
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

import cv2
import mediapipe as mp
import numpy as np

from .config import CameraConfig, DetectionConfig


class DetectionEvent(Enum):
    """Types of detection events."""

    PULLING_DETECTED = "pulling_detected"  # Unified event for all pulling behaviors


@dataclass
class Point3D:
    x: float
    y: float
    z: float

    def distance_to(self, other: "Point3D") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2)


@dataclass
class DetectionResult:
    timestamp: float
    face_detected: bool
    hands_detected: int
    min_hand_face_distance_cm: Optional[float]
    is_pulling_detected: bool
    event: Optional[DetectionEvent]
    processing_time_ms: float


class HandFaceDetector:
    """Trichotillomania-specific pulling detection."""

    # Use forehead landmarks to avoid nose-touch false positives
    FACE_CENTER_LANDMARKS = [10, 9, 151]  # Forehead center points

    # Comprehensive eyebrow region landmarks
    EYEBROW_LANDMARKS = [
        # Left eyebrow - inner to outer
        70,
        63,
        105,
        66,
        107,
        55,
        65,
        52,
        53,
        46,
        35,
        31,
        228,
        229,
        230,
        231,
        232,
        # Right eyebrow - inner to outer
        296,
        334,
        293,
        300,
        276,
        283,
        282,
        295,
        285,
        336,
        285,
        295,
        282,
        283,
        276,
        300,
        293,
        334,
        296,
        261,
        448,
        449,
        450,
        451,
        452,
    ]

    # Extended forehead landmarks for scalp projection
    FOREHEAD_LANDMARKS = [10, 9, 104, 103, 67, 109, 108, 151, 337, 299, 333, 298, 284, 251]

    # Temple region landmarks
    LEFT_TEMPLE_LANDMARKS = [127, 162, 21, 54, 103, 67, 109, 10, 151, 9, 104]
    RIGHT_TEMPLE_LANDMARKS = [356, 389, 251, 284, 332, 297, 338, 10, 151, 9, 333]

    HAND_TIP_INDICES = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

    def __init__(self, detection_config: DetectionConfig, camera_config: CameraConfig):
        """Initialize detector with trichotillomania-specific configuration."""
        self.detection_config = detection_config
        self.camera_config = camera_config

        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=detection_config.confidence_threshold,
            min_tracking_confidence=detection_config.confidence_threshold,
        )
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=detection_config.confidence_threshold,
            min_tracking_confidence=detection_config.confidence_threshold,
        )
        self.cap: Optional[cv2.VideoCapture] = None

    def initialize_camera(self) -> bool:
        """Initialize camera for capture."""
        try:
            # On macOS, provide better error messages
            if sys.platform == "darwin":
                import subprocess

                result = subprocess.run(
                    ["system_profiler", "SPCameraDataType"], capture_output=True, text=True, timeout=5
                )
                if "no devices" in result.stdout.lower():
                    print("❌ No camera devices found. Please check camera connection.")
                    return False

            self.cap = cv2.VideoCapture(self.camera_config.device_id)
            if not self.cap.isOpened():
                if sys.platform == "darwin":
                    print(
                        "❌ Camera access denied. Please grant camera permission in System Preferences > Security & Privacy > Privacy > Camera"
                    )
                else:
                    print("❌ Failed to open camera. Please check camera connection and permissions.")
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_config.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Test read
            ret, _ = self.cap.read()
            if not ret:
                print("❌ Camera opened but cannot read frames. Please check camera permissions.")
                return False

            return True
        except Exception as e:
            print(f"Camera initialization error: {e}")
            return False

    def _normalize_landmark(self, landmark: Any, width: int, height: int) -> Point3D:
        """Convert MediaPipe landmark to 3D point in pixels."""
        return Point3D(
            x=landmark.x * width,
            y=landmark.y * height,
            z=landmark.z * width,
        )

    def _get_face_center(self, face_landmarks: Any, width: int, height: int) -> Point3D:
        """Compute forehead center."""
        pts: List[Point3D] = []
        for idx in self.FACE_CENTER_LANDMARKS:
            if idx < len(face_landmarks.landmark):
                pts.append(self._normalize_landmark(face_landmarks.landmark[idx], width, height))

        if not pts:
            return Point3D(0, 0, 0)

        return Point3D(
            x=sum(p.x for p in pts) / len(pts),
            y=sum(p.y for p in pts) / len(pts),
            z=sum(p.z for p in pts) / len(pts),
        )

    def _get_landmark_region_center(
        self, face_landmarks: Any, indices: List[int], width: int, height: int
    ) -> Point3D:
        """Compute center point of a set of face landmarks."""
        pts: List[Point3D] = []
        for idx in indices:
            if idx < len(face_landmarks.landmark):
                pts.append(self._normalize_landmark(face_landmarks.landmark[idx], width, height))
        if not pts:
            return Point3D(0, 0, 0)
        return Point3D(
            x=sum(p.x for p in pts) / len(pts),
            y=sum(p.y for p in pts) / len(pts),
            z=sum(p.z for p in pts) / len(pts),
        )

    def _get_hair_region_center(self, face_landmarks: Any, width: int, height: int) -> Point3D:
        """Estimate hair/scalp region for trichotillomania detection."""
        forehead_center = self._get_landmark_region_center(face_landmarks, self.FOREHEAD_LANDMARKS, width, height)
        # Project upward to hair region
        return Point3D(
            x=forehead_center.x,
            y=max(0, forehead_center.y - height * 0.15),
            z=forehead_center.z,
        )

    def _get_hand_tips(self, hand_landmarks: Any, width: int, height: int) -> List[Point3D]:
        """Get fingertip points from hand landmarks."""
        tips = []
        for idx in self.HAND_TIP_INDICES:
            if idx < len(hand_landmarks.landmark):
                tips.append(self._normalize_landmark(hand_landmarks.landmark[idx], width, height))
        return tips

    def _pixels_to_cm(self, pixel_distance: float, face_center: Point3D) -> float:
        """Convert pixel distance to centimeters using face size estimation."""
        avg_face_width_pixels = 175
        avg_face_width_cm = 15.0
        depth_factor = max(0.5, min(2.0, 1.0 - face_center.z / 100))
        pixels_per_cm = avg_face_width_pixels / avg_face_width_cm * depth_factor
        return pixel_distance / pixels_per_cm

    def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        """Process single frame for trichotillomania-specific detection."""
        start_time = time.time()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]

        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)

        face_detected = False
        hands_detected = 0
        min_distance_cm: Optional[float] = None
        is_pulling_detected = False
        event: Optional[DetectionEvent] = None
        face_center: Optional[Point3D] = None
        all_hand_tips: List[Point3D] = []

        if face_results.multi_face_landmarks:
            face_detected = True
            face_center = self._get_face_center(face_results.multi_face_landmarks[0], width, height)

        if hand_results.multi_hand_landmarks:
            hands_detected = len(hand_results.multi_hand_landmarks)
            for hand_landmarks in hand_results.multi_hand_landmarks:
                all_hand_tips.extend(self._get_hand_tips(hand_landmarks, width, height))

        # Calculate minimum distance for reference
        if face_center and all_hand_tips:
            min_pixel_distance = min(face_center.distance_to(tip) for tip in all_hand_tips)
            min_distance_cm = self._pixels_to_cm(min_pixel_distance, face_center)

        # Trichotillomania-specific pinch/pull detection
        if face_results.multi_face_landmarks and hand_results.multi_hand_landmarks and face_center:
            fl = face_results.multi_face_landmarks[0]

            # Define detection regions
            eyebrow_center = self._get_landmark_region_center(fl, self.EYEBROW_LANDMARKS, width, height)
            hair_center = self._get_hair_region_center(fl, width, height)
            left_temple = self._get_landmark_region_center(fl, self.LEFT_TEMPLE_LANDMARKS, width, height)
            right_temple = self._get_landmark_region_center(fl, self.RIGHT_TEMPLE_LANDMARKS, width, height)

            # Calculate thresholds based on sensitivity
            base_threshold = self.detection_config.hand_face_threshold_cm * (2.0 - self.detection_config.sensitivity)
            eyebrow_threshold = base_threshold * 0.8  # Closer for eyebrows
            scalp_threshold = base_threshold * 1.2  # Further for scalp/hair
            temple_threshold = base_threshold  # Normal for temples

            # Check for pinching behavior in target regions
            for hand_landmarks in hand_results.multi_hand_landmarks:
                thumb = self._normalize_landmark(hand_landmarks.landmark[4], width, height)
                index = self._normalize_landmark(hand_landmarks.landmark[8], width, height)

                # Calculate pinch distance
                pinch_dist_px = thumb.distance_to(index)
                pinch_dist_cm = self._pixels_to_cm(pinch_dist_px, face_center)

                # Only consider tight pinches (indicating pulling behavior)
                pinch_threshold = 2.5  # cm - tight pinch
                if pinch_dist_cm <= pinch_threshold:
                    pinch_mid = Point3D(
                        x=(thumb.x + index.x) / 2,
                        y=(thumb.y + index.y) / 2,
                        z=(thumb.z + index.z) / 2,
                    )

                    # Check distances to target regions
                    eyebrow_dist_cm = self._pixels_to_cm(eyebrow_center.distance_to(pinch_mid), face_center)
                    hair_dist_cm = self._pixels_to_cm(hair_center.distance_to(pinch_mid), face_center)
                    left_temple_dist_cm = self._pixels_to_cm(left_temple.distance_to(pinch_mid), face_center)
                    right_temple_dist_cm = self._pixels_to_cm(right_temple.distance_to(pinch_mid), face_center)

                    # Detect pulling in any target region
                    if (
                        eyebrow_dist_cm <= eyebrow_threshold
                        or hair_dist_cm <= scalp_threshold
                        or left_temple_dist_cm <= temple_threshold
                        or right_temple_dist_cm <= temple_threshold
                    ):
                        is_pulling_detected = True
                        event = DetectionEvent.PULLING_DETECTED
                        break
        return DetectionResult(
            timestamp=start_time,
            face_detected=face_detected,
            hands_detected=hands_detected,
            min_hand_face_distance_cm=min_distance_cm,
            is_pulling_detected=is_pulling_detected,
            event=event,
            processing_time_ms=(time.time() - start_time) * 1000,
        )

    def capture_and_detect(self) -> Optional[DetectionResult]:
        """Capture frame and perform detection."""
        if not self.cap:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return self.detect_frame(frame)

    def calibrate(self, duration_seconds: int = 10) -> dict:
        """Calibrate detector by measuring baseline distances."""
        if not self.initialize_camera():
            return {"error": "Could not start camera"}

        distances = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration_seconds:
                result = self.capture_and_detect()
                if result and result.min_hand_face_distance_cm is not None:
                    distances.append(result.min_hand_face_distance_cm)
                time.sleep(0.033)
        except Exception as e:
            return {"error": f"Calibration failed: {e}"}
        finally:
            self.cleanup()

        if not distances:
            return {"error": "No calibration data collected"}

        return {
            "samples": len(distances),
            "min_distance": min(distances),
            "max_distance": max(distances),
            "avg_distance": sum(distances) / len(distances),
            "suggested_threshold": sum(distances) / len(distances) * 0.7,
        }

    def cleanup(self) -> None:
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
