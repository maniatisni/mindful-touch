"""Trichotillomania-specific detection using MediaPipe with hybrid segmentation."""

import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional

import cv2
import mediapipe as mp
import numpy as np

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from .config import CameraConfig, DetectionConfig


class DetectionEvent(Enum):
    """Types of detection events."""

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
    debug_info: dict[str, Any]


class HandFaceDetector:
    """
    Trichotillomania-specific pulling detection using a hybrid of 3D landmarks
    and 2D hair segmentation for high accuracy.
    """

    SCALP_CONTACT_LANDMARKS = list(
        set(
            # Forehead landmarks that border the scalp
            [10, 9, 104, 103, 67, 109, 108, 151, 337, 299, 333, 298, 284, 251]
            +
            # Broader temple region landmarks
            [127, 162, 21, 54]  # Left Temple
            + [356, 389, 251, 284]  # Right Temple
        )
    )

    HAND_TIP_INDICES = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky

    # // NEW: Category index for 'hair' in the SelfieMulticlass segmentation model.
    HAIR_CATEGORY_INDEX = 1

    def __init__(self, detection_config: DetectionConfig, camera_config: CameraConfig):
        """Initialize detector with hybrid landmark and segmentation models."""
        self.detection_config = detection_config
        self.camera_config = camera_config

        # Legacy `solutions` API for Face and Hands (as per original code)
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

        # // NEW: Modern `tasks` API for Image Segmenter for precise hair detection.
        # Ensure the model file is in the same directory or provide the full path.
        try:
            segmenter_model_path = "models/selfie_multiclass_256x256.tflite"
            base_options = python.BaseOptions(model_asset_path=segmenter_model_path)
            options = vision.ImageSegmenterOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                output_category_mask=True,  # Crucial for getting the hair mask
            )
            self.segmenter = vision.ImageSegmenter.create_from_options(options)
        except Exception as e:
            print(f"Error initializing ImageSegmenter: {e}")
            print("Please ensure 'selfie_multiclass_256x256.tflite' is downloaded and in the correct path.")
            self.segmenter = None

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
        """Convert MediaPipe landmark to a 3D point in pixel space."""
        # Using width for z is a common practice for pseudo-3D in MediaPipe
        return Point3D(
            x=landmark.x * width,
            y=landmark.y * height,
            z=landmark.z * width,
        )

    # // NEW: Helper to get a list of 3D points for a set of landmark indices.
    def _get_landmarks_as_points(self, landmarks: Any, indices: List[int], width: int, height: int) -> List[Point3D]:
        """Convert a list of landmark indices to a list of Point3D objects."""
        points: List[Point3D] = []
        for idx in indices:
            if idx < len(landmarks.landmark):
                points.append(self._normalize_landmark(landmarks.landmark[idx], width, height))
        return points

    def _get_hand_tips(self, hand_landmarks: Any, width: int, height: int) -> List[Point3D]:
        """Get fingertip points from hand landmarks."""
        tips = []
        for idx in self.HAND_TIP_INDICES:
            if idx < len(hand_landmarks.landmark):
                tips.append(self._normalize_landmark(hand_landmarks.landmark[idx], width, height))
        return tips

    def _pixels_to_cm(self, pixel_distance: float, face_landmarks: Any, width: int, height: int) -> float:
        """Estimate distance in cm. Uses inter-ocular distance for a more stable scale reference."""
        try:
            # Using distance between eyes (landmarks 468 and 473) as a reference
            left_eye = self._normalize_landmark(face_landmarks.landmark[468], width, height)
            right_eye = self._normalize_landmark(face_landmarks.landmark[473], width, height)
            ocular_dist_pixels = left_eye.distance_to(right_eye)

            # Average human inter-ocular distance is ~6.3 cm
            avg_ocular_dist_cm = 6.3

            if ocular_dist_pixels == 0:
                return float("inf")

            pixels_per_cm = ocular_dist_pixels / avg_ocular_dist_cm
            return pixel_distance / pixels_per_cm
        except (IndexError, ZeroDivisionError):
            return float("inf")

    # // MODIFIED: Complete overhaul of the detection logic.
    def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        """Process a single frame using the hybrid landmark and segmentation method."""
        start_time = time.time()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, _ = frame.shape

        # 1. Run all MediaPipe models
        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)

        # 2. Initialize variables for the result
        face_detected = bool(face_results.multi_face_landmarks)
        hands_detected = len(hand_results.multi_hand_landmarks) if hand_results.multi_hand_landmarks else 0
        is_pulling_detected = False
        event: Optional[DetectionEvent] = None
        min_distance_cm: Optional[float] = None
        debug_data = {}

        # 3. Main Detection Logic: Proceed only if face and hands are present
        if face_detected and hands_detected > 0 and self.segmenter:
            face_landmarks = face_results.multi_face_landmarks[0]

            # Get 3D points for hand tips and the scalp contact zone
            all_hand_tips = []
            for hand_landmarks in hand_results.multi_hand_landmarks:
                all_hand_tips.extend(self._get_hand_tips(hand_landmarks, width, height))

            scalp_contact_points = self._get_landmarks_as_points(
                face_landmarks, self.SCALP_CONTACT_LANDMARKS, width, height
            )
            debug_data["scalp_points"] = scalp_contact_points
            debug_data["hand_tips"] = all_hand_tips

            if all_hand_tips and scalp_contact_points:
                # --- Condition 1: 3D Proximity Check ---
                # Find the single fingertip that is closest to the scalp contact zone.
                closest_tip: Optional[Point3D] = None
                min_pixel_dist = float("inf")

                for tip in all_hand_tips:
                    for point in scalp_contact_points:
                        dist = tip.distance_to(point)
                        if dist < min_pixel_dist:
                            min_pixel_dist = dist
                            closest_tip = tip
                            closest_scalp_point = point

                min_distance_cm = self._pixels_to_cm(min_pixel_dist, face_landmarks, width, height)
                debug_data["closest_tip"] = closest_tip
                debug_data["closest_scalp_point"] = closest_scalp_point
                # Check if the hand is physically touching or extremely close to the head.
                # A tight threshold of 2-3 cm is effective for "touch".
                touch_threshold_cm = 2.5 * (2.0 - self.detection_config.sensitivity)  # Sensitivity adjusts threshold

                if min_distance_cm <= touch_threshold_cm and closest_tip is not None:

                    # --- Condition 2: 2D Segmentation Check ---
                    # Convert frame for the segmenter and run it.
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    segmentation_result = self.segmenter.segment(mp_image)

                    # Create a boolean mask where `True` means the pixel is hair.
                    hair_mask = segmentation_result.category_mask.numpy_view() == self.HAIR_CATEGORY_INDEX

                    # Get the 2D pixel coordinates of the closest fingertip.
                    tip_px_x = int(closest_tip.x)
                    tip_px_y = int(closest_tip.y)

                    # Final check: Is the touching finger located on a hair pixel?
                    if 0 <= tip_px_y < height and 0 <= tip_px_x < width:
                        if hair_mask[tip_px_y, tip_px_x]:
                            is_pulling_detected = True
                            event = DetectionEvent.PULLING_DETECTED
        # 4. Return the comprehensive result object
        result = DetectionResult(
            timestamp=start_time,
            face_detected=face_detected,
            hands_detected=hands_detected,
            min_hand_face_distance_cm=min_distance_cm,
            is_pulling_detected=is_pulling_detected,
            event=event,
            processing_time_ms=(time.time() - start_time) * 1000,
            debug_info=debug_data,
        )
        result.debug_info["frame"] = frame
        annotated_frame = self._draw_debug_visualizations(frame, result)
        result.debug_info["frame"] = annotated_frame
        return result

    # The rest of the class methods (capture_and_detect, calibrate, cleanup) remain unchanged.
    def capture_and_detect(self) -> Optional[DetectionResult]:
        """Capture frame and perform detection."""
        if not self.cap or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return self.detect_frame(frame)

    def _draw_debug_visualizations(self, frame: np.ndarray, result: DetectionResult) -> np.ndarray:
        """Draws debugging information onto a frame."""

        # Draw scalp landmarks (the target zone) in green
        for point in result.debug_info.get("scalp_points", []):
            cv2.circle(frame, (int(point.x), int(point.y)), 3, (0, 255, 0), -1)

        # Draw hand landmarks (the source of the action) in blue
        for tip in result.debug_info.get("hand_tips", []):
            cv2.circle(frame, (int(tip.x), int(tip.y)), 5, (255, 0, 0), -1)

        # If a detection is happening, highlight it visually
        if result.is_pulling_detected:
            # Draw a prominent red circle on the closest hand tip
            closest_tip = result.debug_info.get("closest_tip")
            if closest_tip:
                cv2.circle(frame, (int(closest_tip.x), int(closest_tip.y)), 10, (0, 0, 255), 2)

            # Draw a line from the closest tip to the closest scalp point
            closest_scalp_point = result.debug_info.get("closest_scalp_point")
            if closest_tip and closest_scalp_point:
                cv2.line(
                    frame,
                    (int(closest_tip.x), int(closest_tip.y)),
                    (int(closest_scalp_point.x), int(closest_scalp_point.y)),
                    (0, 0, 255),
                    2,
                )

            # Display "PULLING DETECTED" text
            cv2.putText(frame, "PULLING DETECTED", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Display the calculated minimum distance on the top-left of the frame
        if result.min_hand_face_distance_cm is not None:
            dist_text = f"Dist: {result.min_hand_face_distance_cm:.2f} cm"
            cv2.putText(frame, dist_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return frame

    def cleanup(self) -> None:
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None

        # // NEW: Close the segmenter task
        if self.segmenter:
            self.segmenter.close()
