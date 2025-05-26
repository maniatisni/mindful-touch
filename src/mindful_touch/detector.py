"""
Hand-to-face detection using computer vision for Mindful Touch.

This module provides real-time detection of hand proximity to face using
MediaPipe for accurate hand and face landmark detection with geometric
distance calculations.
"""

import math
import time
from typing import List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum

import cv2
import mediapipe as mp
import numpy as np

from .config import DetectionConfig, CameraConfig


class DetectionEvent(Enum):
    """Types of detection events."""
    HAND_NEAR_FACE = "hand_near_face"
    HAND_AWAY_FROM_FACE = "hand_away_from_face"
    FACE_LOST = "face_lost"
    HAND_LOST = "hand_lost"


@dataclass
class Point3D:
    """3D point with x, y, z coordinates."""
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'Point3D') -> float:
        """Calculate Euclidean distance to another point.
        
        Args:
            other: Another 3D point
            
        Returns:
            Distance in the same units as the coordinates
        """
        return math.sqrt(
            (self.x - other.x) ** 2 + 
            (self.y - other.y) ** 2 + 
            (self.z - other.z) ** 2
        )


@dataclass
class DetectionResult:
    """Result of a single detection frame."""
    timestamp: float
    face_detected: bool
    hands_detected: int
    min_hand_face_distance_cm: Optional[float]
    is_hand_near_face: bool
    event: Optional[DetectionEvent]
    confidence: float
    processing_time_ms: float


class HandFaceDetector:
    """Real-time hand-to-face proximity detector using MediaPipe."""
    
    def __init__(
        self, 
        detection_config: DetectionConfig,
        camera_config: CameraConfig
    ):
        """Initialize the hand-face detector.
        
        Args:
            detection_config: Detection parameters configuration
            camera_config: Camera settings configuration
        """
        self.detection_config = detection_config
        self.camera_config = camera_config
        
        # Initialize MediaPipe
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Create MediaPipe instances
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=detection_config.confidence_threshold,
            min_tracking_confidence=detection_config.confidence_threshold
        )
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=detection_config.confidence_threshold,
            min_tracking_confidence=detection_config.confidence_threshold
        )
        
        # Camera and state
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # Detection state tracking
        self._last_detection_time = 0.0
        self._last_hand_near_state = False
        self._calibration_data: List[float] = []
        self._face_center_history: List[Point3D] = []
        
        # Face landmark indices for key points
        self._face_center_landmarks = [1, 2, 5, 6]  # Nose bridge points
        self._face_boundary_landmarks = [10, 151, 9, 8, 168, 6, 152, 175]  # Face outline
        
        print(f"🎯 Hand-face detector initialized")
        print(f"   Sensitivity: {detection_config.sensitivity}")
        print(f"   Threshold: {detection_config.hand_face_threshold_cm}cm")
        print(f"   Confidence: {detection_config.confidence_threshold}")
    
    def initialize_camera(self) -> bool:
        """Initialize the camera for capture.
        
        Returns:
            True if camera was successfully initialized
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_config.device_id)
            
            if not self.cap.isOpened():
                print(f"❌ Could not open camera {self.camera_config.device_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.camera_config.fps)
            
            # Test camera
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Could not read from camera")
                self.cap.release()
                self.cap = None
                return False
            
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"📷 Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False
    
    def _normalize_landmark(self, landmark, image_width: int, image_height: int) -> Point3D:
        """Convert MediaPipe normalized landmark to 3D point.
        
        Args:
            landmark: MediaPipe landmark
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            3D point in pixel coordinates
        """
        return Point3D(
            x=landmark.x * image_width,
            y=landmark.y * image_height,
            z=landmark.z * image_width  # Approximate depth scaling
        )
    
    def _get_face_center(self, face_landmarks, image_width: int, image_height: int) -> Point3D:
        """Calculate the center point of the face.
        
        Args:
            face_landmarks: MediaPipe face landmarks
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            3D point representing face center
        """
        center_points = []
        
        for idx in self._face_center_landmarks:
            if idx < len(face_landmarks.landmark):
                point = self._normalize_landmark(
                    face_landmarks.landmark[idx], 
                    image_width, 
                    image_height
                )
                center_points.append(point)
        
        if not center_points:
            return Point3D(0, 0, 0)
        
        # Calculate average center point
        avg_x = sum(p.x for p in center_points) / len(center_points)
        avg_y = sum(p.y for p in center_points) / len(center_points)
        avg_z = sum(p.z for p in center_points) / len(center_points)
        
        return Point3D(avg_x, avg_y, avg_z)
    
    def _get_hand_tip_points(self, hand_landmarks, image_width: int, image_height: int) -> List[Point3D]:
        """Get fingertip points from hand landmarks.
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            image_width: Image width in pixels
            image_height: Image height in pixels
            
        Returns:
            List of 3D points for fingertips
        """
        # MediaPipe hand landmark indices for fingertips
        tip_indices = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        
        tip_points = []
        for idx in tip_indices:
            if idx < len(hand_landmarks.landmark):
                point = self._normalize_landmark(
                    hand_landmarks.landmark[idx],
                    image_width,
                    image_height
                )
                tip_points.append(point)
        
        return tip_points
    
    def _pixels_to_cm(self, pixel_distance: float, face_center: Point3D) -> float:
        """Convert pixel distance to centimeters using face size estimation.
        
        Args:
            pixel_distance: Distance in pixels
            face_center: Face center point for depth estimation
            
        Returns:
            Estimated distance in centimeters
        """
        # Rough estimation: average human face is about 15cm wide
        # and takes up roughly 150-200 pixels at typical camera distance
        avg_face_width_pixels = 175
        avg_face_width_cm = 15.0
        
        # Adjust for depth (closer faces appear larger)
        depth_factor = max(0.5, min(2.0, 1.0 - face_center.z / 100))
        
        pixels_per_cm = avg_face_width_pixels / avg_face_width_cm * depth_factor
        return pixel_distance / pixels_per_cm
    
    def _calculate_min_hand_face_distance(
        self, 
        face_center: Point3D, 
        hand_tip_points: List[Point3D]
    ) -> float:
        """Calculate minimum distance from any hand point to face center.
        
        Args:
            face_center: Face center point
            hand_tip_points: List of hand tip points
            
        Returns:
            Minimum distance in centimeters
        """
        if not hand_tip_points:
            return float('inf')
        
        min_pixel_distance = min(
            face_center.distance_to(tip) for tip in hand_tip_points
        )
        
        return self._pixels_to_cm(min_pixel_distance, face_center)
    
    def _should_trigger_detection(self, distance_cm: float) -> bool:
        """Determine if distance should trigger a detection event.
        
        Args:
            distance_cm: Distance in centimeters
            
        Returns:
            True if detection should be triggered
        """
        threshold = self.detection_config.hand_face_threshold_cm
        sensitivity = self.detection_config.sensitivity
        
        # Adjust threshold based on sensitivity
        adjusted_threshold = threshold * (2.0 - sensitivity)
        
        return distance_cm <= adjusted_threshold
    
    def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        """Process a single frame for hand-face detection.
        
        Args:
            frame: Input image frame
            
        Returns:
            Detection result for this frame
        """
        start_time = time.time()
        timestamp = start_time
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]
        
        # Process face and hands
        face_results = self.face_mesh.process(rgb_frame)
        hand_results = self.hands.process(rgb_frame)
        
        # Initialize detection values
        face_detected = False
        hands_detected = 0
        min_distance_cm = None
        is_hand_near_face = False
        event = None
        confidence = 0.0
        
        face_center = None
        all_hand_tips = []
        
        # Process face landmarks
        if face_results.multi_face_landmarks:
            face_detected = True
            face_landmarks = face_results.multi_face_landmarks[0]
            face_center = self._get_face_center(face_landmarks, width, height)
            confidence = max(confidence, 0.8)  # Assume high confidence for face
        
        # Process hand landmarks
        if hand_results.multi_hand_landmarks:
            hands_detected = len(hand_results.multi_hand_landmarks)
            
            for hand_landmarks in hand_results.multi_hand_landmarks:
                hand_tips = self._get_hand_tip_points(hand_landmarks, width, height)
                all_hand_tips.extend(hand_tips)
                confidence = max(confidence, 0.8)  # Assume high confidence for hands
        
        # Calculate distance if both face and hands are detected
        if face_center and all_hand_tips:
            min_distance_cm = self._calculate_min_hand_face_distance(
                face_center, all_hand_tips
            )
            is_hand_near_face = self._should_trigger_detection(min_distance_cm)
            
            # Determine event based on state change
            if is_hand_near_face and not self._last_hand_near_state:
                event = DetectionEvent.HAND_NEAR_FACE
            elif not is_hand_near_face and self._last_hand_near_state:
                event = DetectionEvent.HAND_AWAY_FROM_FACE
        else:
            # Handle cases where face or hands are lost
            if not face_detected and self._last_hand_near_state:
                event = DetectionEvent.FACE_LOST
            elif hands_detected == 0 and self._last_hand_near_state:
                event = DetectionEvent.HAND_LOST
        
        # Update state
        self._last_hand_near_state = is_hand_near_face
        self._last_detection_time = timestamp
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        return DetectionResult(
            timestamp=timestamp,
            face_detected=face_detected,
            hands_detected=hands_detected,
            min_hand_face_distance_cm=min_distance_cm,
            is_hand_near_face=is_hand_near_face,
            event=event,
            confidence=confidence,
            processing_time_ms=processing_time_ms
        )
    
    def start_detection(self) -> bool:
        """Start the detection system.
        
        Returns:
            True if detection started successfully
        """
        if not self.initialize_camera():
            return False
        
        self.is_running = True
        print("🎯 Hand-face detection started")
        return True
    
    def stop_detection(self) -> None:
        """Stop the detection system and cleanup resources."""
        self.is_running = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        print("⏹️  Hand-face detection stopped")
    
    def capture_and_detect(self) -> Optional[DetectionResult]:
        """Capture a frame and perform detection.
        
        Returns:
            Detection result or None if capture failed
        """
        if not self.cap or not self.is_running:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            print("⚠️  Failed to capture frame")
            return None
        
        return self.detect_frame(frame)
    
    def calibrate(self, duration_seconds: int = 10) -> dict:
        """Calibrate the detector by measuring baseline distances.
        
        Args:
            duration_seconds: How long to calibrate for
            
        Returns:
            Calibration statistics
        """
        print(f"🎯 Starting calibration for {duration_seconds} seconds...")
        print("   Please sit normally in front of the camera")
        print("   Keep your hands visible and in natural positions")
        
        if not self.start_detection():
            return {"error": "Could not start camera for calibration"}
        
        calibration_data = []
        start_time = time.time()
        frame_count = 0
        detection_count = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                result = self.capture_and_detect()
                frame_count += 1
                
                if result:
                    # Print debug info every 30 frames (about once per second)
                    if frame_count % 30 == 0:
                        elapsed = time.time() - start_time
                        print(f"   {elapsed:.1f}s: Face={result.face_detected}, "
                              f"Hands={result.hands_detected}, "
                              f"Distance={result.min_hand_face_distance_cm}")
                    
                    # Collect data if we have both face and hands detected
                    if (result.face_detected and 
                        result.hands_detected > 0 and 
                        result.min_hand_face_distance_cm is not None):
                        calibration_data.append(result.min_hand_face_distance_cm)
                        detection_count += 1
                
                time.sleep(0.1)  # 10fps for calibration
        
        finally:
            self.stop_detection()
        
        print(f"   Processed {frame_count} frames, collected {len(calibration_data)} distance measurements")
        
        if not calibration_data:
            return {
                "error": "No calibration data collected",
                "debug_info": {
                    "frames_processed": frame_count,
                    "detections_attempted": detection_count,
                    "suggestion": "Try adjusting lighting, moving closer to camera, or ensuring hands are visible"
                }
            }
        
        # Calculate statistics
        sorted_data = sorted(calibration_data)
        stats = {
            "samples": len(calibration_data),
            "min_distance": min(calibration_data),
            "max_distance": max(calibration_data),
            "avg_distance": sum(calibration_data) / len(calibration_data),
            "median_distance": sorted_data[len(sorted_data) // 2],
            "suggested_threshold": sum(calibration_data) / len(calibration_data) * 0.7
        }
        
        print(f"✅ Calibration complete:")
        print(f"   Samples: {stats['samples']}")
        print(f"   Distance range: {stats['min_distance']:.1f}cm - {stats['max_distance']:.1f}cm")
        print(f"   Average distance: {stats['avg_distance']:.1f}cm")
        print(f"   Median distance: {stats['median_distance']:.1f}cm")
        print(f"   Suggested threshold: {stats['suggested_threshold']:.1f}cm")
        
        return stats
    
    def update_config(
        self, 
        detection_config: Optional[DetectionConfig] = None,
        camera_config: Optional[CameraConfig] = None
    ) -> None:
        """Update detector configuration.
        
        Args:
            detection_config: New detection configuration
            camera_config: New camera configuration
        """
        if detection_config:
            self.detection_config = detection_config
            print(f"🔄 Detection config updated - threshold: {detection_config.hand_face_threshold_cm}cm")
        
        if camera_config:
            # Camera config changes require restart
            was_running = self.is_running
            if was_running:
                self.stop_detection()
            
            self.camera_config = camera_config
            
            if was_running:
                self.start_detection()
            
            print(f"🔄 Camera config updated - {camera_config.width}x{camera_config.height}")


def create_detector(
    detection_config: DetectionConfig, 
    camera_config: CameraConfig
) -> HandFaceDetector:
    """Create a hand-face detector with the given configuration.
    
    Args:
        detection_config: Detection parameters
        camera_config: Camera settings
        
    Returns:
        Configured hand-face detector
    """
    return HandFaceDetector(detection_config, camera_config)