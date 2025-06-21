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


class DetectionConstants:
    """Constants for detection algorithm thresholds and parameters."""

    # Distance and size thresholds
    PINCH_THRESHOLD_CM = 2.5
    AVG_FACE_WIDTH_PIXELS = 175
    AVG_FACE_WIDTH_CM = 15.0

    # Velocity filtering
    MAX_PULLING_VELOCITY_PX_PER_SEC = 100.0
    VELOCITY_HISTORY_LENGTH = 5

    # Palm orientation
    PALM_FACING_DOT_THRESHOLD = 0.3  # ~70 degrees

    # Pinch quality analysis
    PINCH_ANGLE_MIN_DEGREES = 60.0
    PINCH_ANGLE_MAX_DEGREES = 120.0

    # Threshold multipliers for different face regions
    EYEBROW_THRESHOLD_MULTIPLIER = 0.8
    SCALP_THRESHOLD_MULTIPLIER = 1.2
    TEMPLE_THRESHOLD_MULTIPLIER = 1.0

    # Hair region projection
    HAIR_REGION_PROJECTION_FACTOR = 0.15

    # Depth estimation
    MIN_DEPTH_FACTOR = 0.5
    MAX_DEPTH_FACTOR = 2.0
    DEPTH_NORMALIZATION_FACTOR = 100


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


class GeometryCalculator:
    """Pure functions for 3D geometry calculations."""

    @staticmethod
    def calculate_cross_product(v1: Point3D, v2: Point3D) -> Point3D:
        """Calculate cross product of two 3D vectors."""
        return Point3D(
            x=v1.y * v2.z - v1.z * v2.y,
            y=v1.z * v2.x - v1.x * v2.z,
            z=v1.x * v2.y - v1.y * v2.x
        )

    @staticmethod
    def calculate_dot_product(v1: Point3D, v2: Point3D) -> float:
        """Calculate dot product of two 3D vectors."""
        return v1.x * v2.x + v1.y * v2.y + v1.z * v2.z

    @staticmethod
    def calculate_magnitude(vector: Point3D) -> float:
        """Calculate magnitude of a 3D vector."""
        return math.sqrt(vector.x**2 + vector.y**2 + vector.z**2)

    @staticmethod
    def normalize_vector(vector: Point3D) -> Optional[Point3D]:
        """Normalize a 3D vector to unit length."""
        magnitude = GeometryCalculator.calculate_magnitude(vector)
        if magnitude == 0:
            return None
        return Point3D(
            x=vector.x / magnitude,
            y=vector.y / magnitude,
            z=vector.z / magnitude
        )

    @staticmethod
    def calculate_angle_between_vectors(v1: Point3D, v2: Point3D) -> Optional[float]:
        """Calculate angle between two vectors in degrees."""
        mag1 = GeometryCalculator.calculate_magnitude(v1)
        mag2 = GeometryCalculator.calculate_magnitude(v2)

        if mag1 == 0 or mag2 == 0:
            return None

        dot_product = GeometryCalculator.calculate_dot_product(v1, v2)
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to valid range

        angle_radians = math.acos(cos_angle)
        return math.degrees(angle_radians)

    @staticmethod
    def create_vector_between_points(start: Point3D, end: Point3D) -> Point3D:
        """Create a vector from start point to end point."""
        return Point3D(
            x=end.x - start.x,
            y=end.y - start.y,
            z=end.z - start.z
        )

    @staticmethod
    def calculate_midpoint(p1: Point3D, p2: Point3D) -> Point3D:
        """Calculate midpoint between two points."""
        return Point3D(
            x=(p1.x + p2.x) / 2,
            y=(p1.y + p2.y) / 2,
            z=(p1.z + p2.z) / 2
        )


@dataclass
class HandAnalysisResult:
    """Result of hand gesture analysis."""
    hand_tips: List[Point3D]
    pinch_distance_px: float
    pinch_midpoint: Optional[Point3D]
    palm_normal: Optional[Point3D]
    velocity_px_per_sec: float
    is_good_pinch_angle: bool
    is_slow_motion: bool


class HandAnalyzer:
    """Analyzes hand gestures and movements."""

    def __init__(self):
        self.geometry = GeometryCalculator()
        self._hand_positions_history: List[List[Point3D]] = []
        self._position_timestamps: List[float] = []

    def analyze_hand_gesture(self, hand_landmarks: Any, width: int, height: int,
                           current_time: float, face_center: Point3D) -> HandAnalysisResult:
        """Analyze a single hand gesture for pulling behavior indicators."""
        # Get hand tips
        hand_tips = self._get_hand_tips(hand_landmarks, width, height)

        # Calculate velocity
        velocity = self._calculate_hand_velocity(hand_tips, current_time)
        is_slow_motion = velocity <= DetectionConstants.MAX_PULLING_VELOCITY_PX_PER_SEC

        # Analyze pinch quality
        pinch_distance_px, is_good_pinch_angle = self._analyze_pinch_quality(
            hand_landmarks, width, height
        )

        # Get pinch midpoint if it's a valid pinch
        pinch_midpoint = None
        if pinch_distance_px <= self._pixels_to_cm(
            DetectionConstants.PINCH_THRESHOLD_CM * DetectionConstants.AVG_FACE_WIDTH_PIXELS / DetectionConstants.AVG_FACE_WIDTH_CM,
            face_center
        ):
            thumb = self._normalize_landmark(hand_landmarks.landmark[4], width, height)
            index = self._normalize_landmark(hand_landmarks.landmark[8], width, height)
            pinch_midpoint = self.geometry.calculate_midpoint(thumb, index)

        # Calculate palm orientation
        palm_normal = self._get_palm_normal(hand_landmarks, width, height)

        return HandAnalysisResult(
            hand_tips=hand_tips,
            pinch_distance_px=pinch_distance_px,
            pinch_midpoint=pinch_midpoint,
            palm_normal=palm_normal,
            velocity_px_per_sec=velocity,
            is_good_pinch_angle=is_good_pinch_angle,
            is_slow_motion=is_slow_motion
        )

    def _normalize_landmark(self, landmark: Any, width: int, height: int) -> Point3D:
        """Convert MediaPipe landmark to 3D point in pixels."""
        return Point3D(
            x=landmark.x * width,
            y=landmark.y * height,
            z=landmark.z * width,
        )

    def _get_hand_tips(self, hand_landmarks: Any, width: int, height: int) -> List[Point3D]:
        """Get fingertip points from hand landmarks."""
        tips = []
        hand_tip_indices = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        for idx in hand_tip_indices:
            if idx < len(hand_landmarks.landmark):
                tips.append(self._normalize_landmark(hand_landmarks.landmark[idx], width, height))
        return tips

    def _get_palm_normal(self, hand_landmarks: Any, width: int, height: int) -> Optional[Point3D]:
        """Calculate palm normal vector to determine hand orientation."""
        try:
            wrist = self._normalize_landmark(hand_landmarks.landmark[0], width, height)
            middle_mcp = self._normalize_landmark(hand_landmarks.landmark[9], width, height)
            index_mcp = self._normalize_landmark(hand_landmarks.landmark[5], width, height)

            v1 = self.geometry.create_vector_between_points(wrist, middle_mcp)
            v2 = self.geometry.create_vector_between_points(wrist, index_mcp)

            normal = self.geometry.calculate_cross_product(v1, v2)
            return self.geometry.normalize_vector(normal)

        except (IndexError, ZeroDivisionError):
            return None

    def _analyze_pinch_quality(self, hand_landmarks: Any, width: int, height: int) -> tuple[float, bool]:
        """Analyze pinch gesture quality including angle and pressure indicators."""
        try:
            thumb_tip = self._normalize_landmark(hand_landmarks.landmark[4], width, height)
            thumb_ip = self._normalize_landmark(hand_landmarks.landmark[3], width, height)
            index_tip = self._normalize_landmark(hand_landmarks.landmark[8], width, height)
            index_pip = self._normalize_landmark(hand_landmarks.landmark[6], width, height)

            pinch_distance = thumb_tip.distance_to(index_tip)

            thumb_vector = self.geometry.create_vector_between_points(thumb_ip, thumb_tip)
            index_vector = self.geometry.create_vector_between_points(index_pip, index_tip)

            angle_degrees = self.geometry.calculate_angle_between_vectors(thumb_vector, index_vector)

            if angle_degrees is not None:
                is_good_pinch_angle = (
                    DetectionConstants.PINCH_ANGLE_MIN_DEGREES <= angle_degrees <=
                    DetectionConstants.PINCH_ANGLE_MAX_DEGREES
                )
                return pinch_distance, is_good_pinch_angle

            return pinch_distance, True

        except (IndexError, ValueError, ZeroDivisionError):
            thumb_tip = self._normalize_landmark(hand_landmarks.landmark[4], width, height)
            index_tip = self._normalize_landmark(hand_landmarks.landmark[8], width, height)
            return thumb_tip.distance_to(index_tip), True

    def _calculate_hand_velocity(self, current_hand_tips: List[Point3D], current_time: float) -> float:
        """Calculate average velocity of hand movement to filter quick gestures."""
        if len(self._hand_positions_history) < 2:
            self._hand_positions_history.append(current_hand_tips)
            self._position_timestamps.append(current_time)
            return 0.0

        self._hand_positions_history.append(current_hand_tips)
        self._position_timestamps.append(current_time)

        if len(self._hand_positions_history) > DetectionConstants.VELOCITY_HISTORY_LENGTH:
            self._hand_positions_history.pop(0)
            self._position_timestamps.pop(0)

        if len(self._hand_positions_history) < 2:
            return 0.0

        total_distance = 0.0
        total_time = 0.0

        for i in range(1, len(self._hand_positions_history)):
            prev_tips = self._hand_positions_history[i-1]
            curr_tips = self._hand_positions_history[i]
            time_diff = self._position_timestamps[i] - self._position_timestamps[i-1]

            if time_diff <= 0 or len(prev_tips) == 0 or len(curr_tips) == 0:
                continue

            frame_distance = 0.0
            tip_count = 0

            for j in range(min(len(prev_tips), len(curr_tips), 2)):
                distance = prev_tips[j].distance_to(curr_tips[j])
                frame_distance += distance
                tip_count += 1

            if tip_count > 0:
                frame_distance /= tip_count
                total_distance += frame_distance
                total_time += time_diff

        if total_time > 0:
            return total_distance / total_time

        return 0.0

    @staticmethod
    def _pixels_to_cm(pixel_distance: float, face_center: Point3D) -> float:
        """Convert pixel distance to centimeters using face size estimation."""
        depth_factor = max(
            DetectionConstants.MIN_DEPTH_FACTOR,
            min(DetectionConstants.MAX_DEPTH_FACTOR,
                1.0 - face_center.z / DetectionConstants.DEPTH_NORMALIZATION_FACTOR)
        )
        pixels_per_cm = (DetectionConstants.AVG_FACE_WIDTH_PIXELS /
                        DetectionConstants.AVG_FACE_WIDTH_CM * depth_factor)
        return pixel_distance / pixels_per_cm


@dataclass
class FaceRegions:
    """Container for face target regions."""
    center: Point3D
    eyebrow_center: Point3D
    hair_center: Point3D
    left_temple: Point3D
    right_temple: Point3D


class FaceRegionDetector:
    """Manages face landmark detection and region calculations."""

    # Face landmark indices
    FACE_CENTER_LANDMARKS = [10, 9, 151]  # Forehead center points
    EYEBROW_LANDMARKS = [
        70, 63, 105, 66, 107, 55, 65, 52, 53, 46, 35, 31, 228, 229, 230, 231, 232,
        296, 334, 293, 300, 276, 283, 282, 295, 285, 336, 285, 295, 282, 283, 276,
        300, 293, 334, 296, 261, 448, 449, 450, 451, 452,
    ]
    FOREHEAD_LANDMARKS = [10, 9, 104, 103, 67, 109, 108, 151, 337, 299, 333, 298, 284, 251]
    LEFT_TEMPLE_LANDMARKS = [127, 162, 21, 54, 103, 67, 109, 10, 151, 9, 104]
    RIGHT_TEMPLE_LANDMARKS = [356, 389, 251, 284, 332, 297, 338, 10, 151, 9, 333]

    def __init__(self):
        self.geometry = GeometryCalculator()

    def extract_face_regions(self, face_landmarks: Any, width: int, height: int) -> FaceRegions:
        """Extract all target regions from face landmarks."""
        face_center = self._get_face_center(face_landmarks, width, height)
        eyebrow_center = self._get_landmark_region_center(
            face_landmarks, self.EYEBROW_LANDMARKS, width, height
        )
        hair_center = self._get_hair_region_center(face_landmarks, width, height)
        left_temple = self._get_landmark_region_center(
            face_landmarks, self.LEFT_TEMPLE_LANDMARKS, width, height
        )
        right_temple = self._get_landmark_region_center(
            face_landmarks, self.RIGHT_TEMPLE_LANDMARKS, width, height
        )

        return FaceRegions(
            center=face_center,
            eyebrow_center=eyebrow_center,
            hair_center=hair_center,
            left_temple=left_temple,
            right_temple=right_temple
        )

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
        forehead_center = self._get_landmark_region_center(
            face_landmarks, self.FOREHEAD_LANDMARKS, width, height
        )
        # Project upward to hair region
        return Point3D(
            x=forehead_center.x,
            y=max(0, forehead_center.y - height * DetectionConstants.HAIR_REGION_PROJECTION_FACTOR),
            z=forehead_center.z,
        )


class DetectionFilter:
    """Applies filtering logic to determine if pulling behavior is detected."""

    def __init__(self, detection_config: DetectionConfig):
        self.detection_config = detection_config
        self.geometry = GeometryCalculator()

    def evaluate_pulling_behavior(
        self,
        hand_analysis: HandAnalysisResult,
        face_regions: FaceRegions
    ) -> bool:
        """Evaluate if the hand gesture indicates pulling behavior."""
        # Must have a valid pinch
        if not hand_analysis.pinch_midpoint:
            return False

        # Must have good pinch angle and slow motion
        if not (hand_analysis.is_good_pinch_angle and hand_analysis.is_slow_motion):
            return False

        # Must have valid palm orientation
        if not hand_analysis.palm_normal:
            return False

        # Calculate thresholds based on sensitivity
        base_threshold = self.detection_config.hand_face_threshold_cm * (
            2.0 - self.detection_config.sensitivity
        )
        eyebrow_threshold = base_threshold * DetectionConstants.EYEBROW_THRESHOLD_MULTIPLIER
        scalp_threshold = base_threshold * DetectionConstants.SCALP_THRESHOLD_MULTIPLIER
        temple_threshold = base_threshold * DetectionConstants.TEMPLE_THRESHOLD_MULTIPLIER

        # Check distances to target regions
        pinch_mid = hand_analysis.pinch_midpoint
        face_center = face_regions.center

        eyebrow_dist_cm = self._pixels_to_cm(
            face_regions.eyebrow_center.distance_to(pinch_mid), face_center
        )
        hair_dist_cm = self._pixels_to_cm(
            face_regions.hair_center.distance_to(pinch_mid), face_center
        )
        left_temple_dist_cm = self._pixels_to_cm(
            face_regions.left_temple.distance_to(pinch_mid), face_center
        )
        right_temple_dist_cm = self._pixels_to_cm(
            face_regions.right_temple.distance_to(pinch_mid), face_center
        )

        # Check if palm is facing any target region for pulling behavior
        palm_facing_eyebrow = self._is_palm_facing_target(
            hand_analysis.palm_normal, pinch_mid, face_regions.eyebrow_center
        )
        palm_facing_hair = self._is_palm_facing_target(
            hand_analysis.palm_normal, pinch_mid, face_regions.hair_center
        )
        palm_facing_left_temple = self._is_palm_facing_target(
            hand_analysis.palm_normal, pinch_mid, face_regions.left_temple
        )
        palm_facing_right_temple = self._is_palm_facing_target(
            hand_analysis.palm_normal, pinch_mid, face_regions.right_temple
        )

        # Detect pulling in any target region only if palm is oriented correctly
        return (
            (eyebrow_dist_cm <= eyebrow_threshold and palm_facing_eyebrow)
            or (hair_dist_cm <= scalp_threshold and palm_facing_hair)
            or (left_temple_dist_cm <= temple_threshold and palm_facing_left_temple)
            or (right_temple_dist_cm <= temple_threshold and palm_facing_right_temple)
        )

    def _is_palm_facing_target(
        self, palm_normal: Point3D, hand_center: Point3D, target_center: Point3D
    ) -> bool:
        """Check if palm is oriented toward the target region."""
        if not palm_normal:
            return True  # Default to allow if we can't determine orientation

        # Vector from hand to target
        hand_to_target = self.geometry.create_vector_between_points(hand_center, target_center)
        hand_to_target_normalized = self.geometry.normalize_vector(hand_to_target)

        if not hand_to_target_normalized:
            return True

        # Dot product to check alignment
        dot_product = self.geometry.calculate_dot_product(palm_normal, hand_to_target_normalized)

        # Palm should be roughly facing the target
        return dot_product > DetectionConstants.PALM_FACING_DOT_THRESHOLD

    @staticmethod
    def _pixels_to_cm(pixel_distance: float, face_center: Point3D) -> float:
        """Convert pixel distance to centimeters using face size estimation."""
        depth_factor = max(
            DetectionConstants.MIN_DEPTH_FACTOR,
            min(DetectionConstants.MAX_DEPTH_FACTOR,
                1.0 - face_center.z / DetectionConstants.DEPTH_NORMALIZATION_FACTOR)
        )
        pixels_per_cm = (DetectionConstants.AVG_FACE_WIDTH_PIXELS /
                        DetectionConstants.AVG_FACE_WIDTH_CM * depth_factor)
        return pixel_distance / pixels_per_cm


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
    """Trichotillomania-specific pulling detection using modular components."""

    def __init__(self, detection_config: DetectionConfig, camera_config: CameraConfig):
        """Initialize detector with trichotillomania-specific configuration."""
        self.detection_config = detection_config
        self.camera_config = camera_config

        # Initialize MediaPipe components
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

        # Initialize detection components
        self.hand_analyzer = HandAnalyzer()
        self.face_detector = FaceRegionDetector()
        self.detection_filter = DetectionFilter(detection_config)

    def initialize_camera(self) -> bool:
        """Initialize camera for capture."""
        try:
            # On macOS, provide better error messages
            if sys.platform == "darwin":
                import subprocess

                result = subprocess.run(["system_profiler", "SPCameraDataType"], capture_output=True, text=True, timeout=5)
                if "no devices" in result.stdout.lower():
                    print("❌ No camera devices found. Please check camera connection.")
                    return False

            self.cap = cv2.VideoCapture(self.camera_config.device_id)
            if not self.cap.isOpened():
                if sys.platform == "darwin":
                    print("❌ Camera access denied. Please grant camera permission in System Preferences > Security & Privacy > Privacy > Camera")
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

    def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        """Process single frame for trichotillomania-specific detection using modular components."""
        start_time = time.time()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]

        # 1. Extract landmarks from MediaPipe
        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)

        # 2. Initialize detection variables
        face_detected = bool(face_results.multi_face_landmarks)
        hands_detected = len(hand_results.multi_hand_landmarks) if hand_results.multi_hand_landmarks else 0
        min_distance_cm: Optional[float] = None
        is_pulling_detected = False
        event: Optional[DetectionEvent] = None

        # 3. Process face landmarks if available
        face_regions = None
        if face_results.multi_face_landmarks:
            face_regions = self.face_detector.extract_face_regions(
                face_results.multi_face_landmarks[0], width, height
            )

        # 4. Process hand landmarks and detect pulling behavior
        if hand_results.multi_hand_landmarks and face_regions:
            all_hand_tips: List[Point3D] = []

            for hand_landmarks in hand_results.multi_hand_landmarks:
                # Analyze hand gesture
                hand_analysis = self.hand_analyzer.analyze_hand_gesture(
                    hand_landmarks, width, height, start_time, face_regions.center
                )

                # Accumulate hand tips for distance calculation
                all_hand_tips.extend(hand_analysis.hand_tips)

                # Check if this hand indicates pulling behavior
                if self.detection_filter.evaluate_pulling_behavior(hand_analysis, face_regions):
                    is_pulling_detected = True
                    event = DetectionEvent.PULLING_DETECTED
                    break

            # Calculate minimum distance for reference
            if all_hand_tips:
                min_pixel_distance = min(
                    face_regions.center.distance_to(tip) for tip in all_hand_tips
                )
                min_distance_cm = HandAnalyzer._pixels_to_cm(min_pixel_distance, face_regions.center)

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

    def cleanup(self) -> None:
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None
