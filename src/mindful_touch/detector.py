"""Hand-to-face detection using MediaPipe."""

import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np

from .config import CameraConfig, DetectionConfig


class DetectionEvent(Enum):
    HAND_NEAR_FACE = "hand_near_face"
    HAND_AWAY_FROM_FACE = "hand_away_from_face"


@dataclass
class Point3D:
    x: float
    y: float
    z: float
    
    def distance_to(self, other: "Point3D") -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


@dataclass
class DetectionResult:
    timestamp: float
    face_detected: bool
    hands_detected: int
    min_hand_face_distance_cm: Optional[float]
    is_hand_near_face: bool
    event: Optional[DetectionEvent]
    processing_time_ms: float
    frame: Optional[np.ndarray] = None


class HandFaceDetector:
    """Real-time hand-to-face proximity detector."""
    
    # Key face landmarks for detection
    FACE_CENTER_LANDMARKS = [1, 2, 5, 6]  # Nose bridge
    # Hand tip landmarks
    HAND_TIP_INDICES = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
    
    def __init__(self, detection_config: DetectionConfig, camera_config: CameraConfig):
        self.detection_config = detection_config
        self.camera_config = camera_config
        
        # Initialize MediaPipe
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=detection_config.confidence_threshold,
            min_tracking_confidence=detection_config.confidence_threshold
        )
        
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=detection_config.confidence_threshold,
            min_tracking_confidence=detection_config.confidence_threshold
        )
        
        self.cap: Optional[cv2.VideoCapture] = None
        self._last_hand_near_state = False
        
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
        except:
            return False
    
    def _normalize_landmark(self, landmark, width: int, height: int) -> Point3D:
        """Convert MediaPipe landmark to 3D point."""
        return Point3D(
            x=landmark.x * width,
            y=landmark.y * height,
            z=landmark.z * width  # Approximate depth
        )
    
    def _get_face_center(self, face_landmarks, width: int, height: int) -> Point3D:
        """Calculate face center from landmarks."""
        points = []
        for idx in self.FACE_CENTER_LANDMARKS:
            if idx < len(face_landmarks.landmark):
                points.append(self._normalize_landmark(face_landmarks.landmark[idx], width, height))
        
        if not points:
            return Point3D(0, 0, 0)
            
        return Point3D(
            x=sum(p.x for p in points) / len(points),
            y=sum(p.y for p in points) / len(points),
            z=sum(p.z for p in points) / len(points)
        )
    
    def _get_hand_tips(self, hand_landmarks, width: int, height: int) -> List[Point3D]:
        """Get fingertip points from hand landmarks."""
        tips = []
        for idx in self.HAND_TIP_INDICES:
            if idx < len(hand_landmarks.landmark):
                tips.append(self._normalize_landmark(hand_landmarks.landmark[idx], width, height))
        return tips
    
    def _pixels_to_cm(self, pixel_distance: float, face_center: Point3D) -> float:
        """Convert pixel distance to centimeters using face size estimation.
        
        Assumes average face width of 15cm at ~175 pixels
        """
        avg_face_width_pixels = 175
        avg_face_width_cm = 15.0
        
        # Simple depth adjustment
        depth_factor = max(0.5, min(2.0, 1.0 - face_center.z / 100))
        pixels_per_cm = avg_face_width_pixels / avg_face_width_cm * depth_factor
        
        return pixel_distance / pixels_per_cm
    
    def detect_frame(self, frame: np.ndarray) -> DetectionResult:
        """Process single frame for detection."""
        start_time = time.time()
        
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
        
        face_center = None
        all_hand_tips = []
        
        # Process face
        if face_results.multi_face_landmarks:
            face_detected = True
            face_center = self._get_face_center(face_results.multi_face_landmarks[0], width, height)
        
        # Process hands
        if hand_results.multi_hand_landmarks:
            hands_detected = len(hand_results.multi_hand_landmarks)
            for hand_landmarks in hand_results.multi_hand_landmarks:
                all_hand_tips.extend(self._get_hand_tips(hand_landmarks, width, height))
        
        # Calculate distance if both detected
        if face_center and all_hand_tips:
            min_pixel_distance = min(face_center.distance_to(tip) for tip in all_hand_tips)
            min_distance_cm = self._pixels_to_cm(min_pixel_distance, face_center)
            
            # Adjust threshold by sensitivity
            adjusted_threshold = self.detection_config.hand_face_threshold_cm * (2.0 - self.detection_config.sensitivity)
            is_hand_near_face = min_distance_cm <= adjusted_threshold
            
            # Determine event
            if is_hand_near_face and not self._last_hand_near_state:
                event = DetectionEvent.HAND_NEAR_FACE
            elif not is_hand_near_face and self._last_hand_near_state:
                event = DetectionEvent.HAND_AWAY_FROM_FACE
        
        self._last_hand_near_state = is_hand_near_face
        
        return DetectionResult(
            timestamp=start_time,
            face_detected=face_detected,
            hands_detected=hands_detected,
            min_hand_face_distance_cm=min_distance_cm,
            is_hand_near_face=is_hand_near_face,
            event=event,
            processing_time_ms=(time.time() - start_time) * 1000
        )
    
    def capture_and_detect(self) -> Optional[DetectionResult]:
        """Capture frame and perform detection."""
        if not self.cap:
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        return self.detect_frame(frame)
    
    def get_annotated_frame(self, frame: np.ndarray, result: DetectionResult) -> np.ndarray:
        """Add visual annotations to frame."""
        annotated = frame.copy()
        height, width = frame.shape[:2]
        
        # Status text
        status = "PULLING DETECTED!" if result.is_hand_near_face else "Monitoring..."
        color = (0, 0, 255) if result.is_hand_near_face else (0, 255, 0)
        cv2.putText(annotated, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        
        # Distance
        if result.min_hand_face_distance_cm is not None:
            dist_text = f"Distance: {result.min_hand_face_distance_cm:.1f}cm"
            cv2.putText(annotated, dist_text, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        return annotated
    
    def calibrate(self, duration_seconds: int = 10) -> dict:
        """Calibrate detector by measuring baseline distances."""
        if not self.initialize_camera():
            return {"error": "Could not start camera"}
        
        distances = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            result = self.capture_and_detect()
            if result and result.min_hand_face_distance_cm is not None:
                distances.append(result.min_hand_face_distance_cm)
            time.sleep(0.033)
        
        self.cleanup()
        
        if not distances:
            return {"error": "No calibration data collected"}
        
        return {
            "samples": len(distances),
            "min_distance": min(distances),
            "max_distance": max(distances),
            "avg_distance": sum(distances) / len(distances),
            "suggested_threshold": sum(distances) / len(distances) * 0.7
        }
    
    def cleanup(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
            self.cap = None