"""Simplified hand-to-face detection using MediaPipe."""

import math
import time
from dataclasses import dataclass
from typing import Any, List, Optional

import cv2
import mediapipe as mp
import numpy as np

from .config import CameraConfig, DetectionConfig


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
    is_hand_near_face: bool
    processing_time_ms: float


class HandFaceDetector:
    """Simplified hand-to-face proximity detector."""

    # Use forehead landmarks to avoid nose-touch false positives
    FACE_CENTER_LANDMARKS = [10, 9, 151]  # Forehead center points
    HAND_TIP_INDICES = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

    def __init__(self, detection_config: DetectionConfig, camera_config: CameraConfig):
        """Initialize detector."""
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
            self.cap = cv2.VideoCapture(self.camera_config.device_id)
            if not self.cap.isOpened():
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_config.fps)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            ret, _ = self.cap.read()
            return ret
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
        """Process single frame for detection."""
        start_time = time.time()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]

        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)

        face_detected = False
        hands_detected = 0
        min_distance_cm: Optional[float] = None
        is_hand_near_face = False
        face_center: Optional[Point3D] = None
        all_hand_tips: List[Point3D] = []

        if face_results.multi_face_landmarks:
            face_detected = True
            face_center = self._get_face_center(face_results.multi_face_landmarks[0], width, height)

        if hand_results.multi_hand_landmarks:
            hands_detected = len(hand_results.multi_hand_landmarks)
            for hand_landmarks in hand_results.multi_hand_landmarks:
                all_hand_tips.extend(self._get_hand_tips(hand_landmarks, width, height))

        # Simple proximity detection
        if face_center and all_hand_tips:
            min_pixel_distance = min(face_center.distance_to(tip) for tip in all_hand_tips)
            min_distance_cm = self._pixels_to_cm(min_pixel_distance, face_center)

            # Apply sensitivity adjustment
            adjusted_threshold = self.detection_config.hand_face_threshold_cm * (
                2.0 - self.detection_config.sensitivity
            )
            is_hand_near_face = min_distance_cm <= adjusted_threshold

        return DetectionResult(
            timestamp=start_time,
            face_detected=face_detected,
            hands_detected=hands_detected,
            min_hand_face_distance_cm=min_distance_cm,
            is_hand_near_face=is_hand_near_face,
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
