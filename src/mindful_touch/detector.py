"""Trichotillomania-specific detection using a robust, hybrid approach without dwell time."""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .config import CameraConfig, DetectionConfig


class DetectionEvent(Enum):
    PULLING_DETECTED = "pulling_detected"


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
    debug_info: Dict[str, Any] = field(default_factory=dict)


class HandFaceDetector:
    """Implements a robust, stateless, three-stage detection for hair pulling."""

    FACE_MESH_LANDMARKS_FOR_PROXIMITY = list(range(468))
    HAIR_CATEGORY_INDEX = 1
    HAND_CONTACT_INDICES = [4, 8, 12, 16, 20, 5, 6, 9, 10, 13, 14, 17, 18]

    def __init__(
        self,
        detection_config: DetectionConfig,
        camera_config: CameraConfig,
        model_path: str = "models/selfie_multiclass_256x256.tflite",
    ):
        self.detection_config = detection_config
        self.camera_config = camera_config

        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5
        )

        try:
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.ImageSegmenterOptions(
                base_options=base_options, running_mode=vision.RunningMode.IMAGE, output_category_mask=True
            )
            self.segmenter = vision.ImageSegmenter.create_from_options(options)
        except Exception as e:
            print(f"FATAL: Could not initialize ImageSegmenter. Error: {e}")
            self.segmenter = None

        self.cap: Optional[cv2.VideoCapture] = None

    def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        start_time = time.time()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, _ = frame.shape

        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)

        is_pulling_detected = False
        min_dist_cm = None
        debug_data = {"proximity_ok": False, "hair_touch_ok": False}
        face_detected = bool(face_results.multi_face_landmarks)
        hands_detected = len(hand_results.multi_hand_landmarks) if hand_results.multi_hand_landmarks else 0

        if face_detected and hands_detected > 0 and self.segmenter:
            face_landmarks_data = face_results.multi_face_landmarks[0]
            face_points = self._get_landmarks_as_points(
                face_landmarks_data, self.FACE_MESH_LANDMARKS_FOR_PROXIMITY, width, height
            )
            hand_contact_points = [
                point
                for hand_lm in hand_results.multi_hand_landmarks
                for point in self._get_landmarks_as_points(hand_lm, self.HAND_CONTACT_INDICES, width, height)
            ]

            if face_points and hand_contact_points:
                min_pixel_dist, _, _ = self._find_closest_points(hand_contact_points, face_points)
                min_dist_cm = self._pixels_to_cm(min_pixel_dist, face_landmarks_data, width, height)

                proximity_threshold_cm = self.detection_config.hand_face_threshold_cm
                if min_dist_cm is not None and min_dist_cm <= proximity_threshold_cm:
                    debug_data["proximity_ok"] = True

                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    segmentation_result = self.segmenter.segment(mp_image)
                    hair_mask = segmentation_result.category_mask.numpy_view() == self.HAIR_CATEGORY_INDEX
                    debug_data["hair_mask"] = hair_mask

                    is_touching_hair_now = self._check_contact_in_hair_zone(
                        hand_contact_points, hair_mask, height, width
                    )
                    if is_touching_hair_now:
                        debug_data["hair_touch_ok"] = True
                        is_pulling_detected = True

        result = DetectionResult(
            timestamp=start_time,
            face_detected=face_detected,
            hands_detected=hands_detected,
            min_hand_face_distance_cm=min_dist_cm,
            is_pulling_detected=is_pulling_detected,
            event=DetectionEvent.PULLING_DETECTED if is_pulling_detected else None,
            processing_time_ms=(time.time() - start_time) * 1000,
            debug_info=debug_data,
        )

        annotated_frame = self._draw_debug_visualizations(frame.copy(), result)
        result.debug_info["frame"] = annotated_frame
        return result

    def _check_contact_in_hair_zone(
        self, contact_points: List[Point3D], hair_mask: np.ndarray, height: int, width: int
    ) -> bool:
        neighborhood_size = 2
        for point in contact_points:
            x, y = int(point.x), int(point.y)
            y_min, y_max = max(0, y - neighborhood_size), min(height, y + neighborhood_size + 1)
            x_min, x_max = max(0, x - neighborhood_size), min(width, x + neighborhood_size + 1)
            if y_min < y_max and x_min < x_max:
                if np.any(hair_mask[y_min:y_max, x_min:x_max]):
                    return True
        return False

    def _draw_debug_visualizations(self, frame: np.ndarray, result: DetectionResult) -> np.ndarray:
        debug_info = result.debug_info
        hair_mask = debug_info.get("hair_mask")

        if hair_mask is not None:
            color_mask = np.zeros_like(frame, dtype=np.uint8)
            color_mask[hair_mask] = (128, 0, 128)
            frame = cv2.addWeighted(frame, 1.0, color_mask, 0.4, 0)

        prox_ok = debug_info.get("proximity_ok", False)
        prox_color = (0, 255, 0) if prox_ok else (0, 165, 255)
        cv2.putText(frame, f"Proximity OK: {prox_ok}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, prox_color, 2)

        hair_touch_ok = debug_info.get("hair_touch_ok", False)
        hair_color = (0, 255, 0) if hair_touch_ok else (0, 165, 255)
        cv2.putText(frame, f"Hair Touch OK: {hair_touch_ok}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, hair_color, 2)

        if result.is_pulling_detected:
            cv2.putText(frame, "PULLING DETECTED", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        return frame

    def initialize_camera(self) -> bool:
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
        return Point3D(x=landmark.x * width, y=landmark.y * height, z=landmark.z * width)

    def _get_landmarks_as_points(self, landmarks: Any, indices: List[int], width: int, height: int) -> List[Point3D]:
        return [
            self._normalize_landmark(landmarks.landmark[idx], width, height)
            for idx in indices
            if idx < len(landmarks.landmark)
        ]

    def _find_closest_points(self, points1: List[Point3D], points2: List[Point3D]):
        min_dist = float("inf")
        closest_p1, closest_p2 = None, None
        for p1 in points1:
            for p2 in points2:
                dist = p1.distance_to(p2)
                if dist < min_dist:
                    min_dist = dist
                    closest_p1, closest_p2 = p1, p2
        return min_dist, closest_p1, closest_p2

    def _pixels_to_cm(self, pixel_distance: float, face_landmarks: Any, width: int, height: int) -> float:
        try:
            p_right = self._normalize_landmark(face_landmarks.landmark[473], width, height)
            p_left = self._normalize_landmark(face_landmarks.landmark[468], width, height)
            ocular_dist_pixels = p_left.distance_to(p_right)
            if ocular_dist_pixels == 0:
                return float("inf")
            pixels_per_cm = ocular_dist_pixels / 6.3
            return pixel_distance / pixels_per_cm
        except (IndexError, ZeroDivisionError):
            return float("inf")

    def capture_and_detect(self) -> Optional[DetectionResult]:
        if not self.cap or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return self.detect_frame(frame)

    def cleanup(self) -> None:
        if self.cap:
            self.cap.release()
        if self.segmenter:
            self.segmenter.close()
        self.cap = None
