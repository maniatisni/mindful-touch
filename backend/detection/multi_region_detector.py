"""
Multi-Region Detector for Mindful Touch
Clean implementation supporting multiple facial regions
"""

import time
from typing import Any, Dict, List, Tuple

import cv2
import mediapipe as mp
import numpy as np

from .config import Config


class MultiRegionDetector:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        # Create MediaPipe instances
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            model_complexity=1,
            min_detection_confidence=Config.HAND_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.HAND_TRACKING_CONFIDENCE,
        )

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=Config.FACE_DETECTION_CONFIDENCE,
            min_tracking_confidence=Config.FACE_TRACKING_CONFIDENCE,
        )

        # Detection state for each region
        self.region_states = {}
        for region in Config.AVAILABLE_REGIONS:
            self.region_states[region] = {"contact_start_time": None, "alert_active": False, "last_alert_time": 0}

        # Fingertip indices
        self.FINGERTIPS = [4, 8, 12, 16, 20]

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Process frame with multi-region detection"""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        # Run detection
        hand_results = self.hands.process(rgb_frame)
        face_results = self.face_mesh.process(rgb_frame)

        # Convert back to BGR
        rgb_frame.flags.writeable = True
        annotated_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        # Extract landmarks
        hand_landmarks = self._extract_hand_landmarks(hand_results, frame.shape)
        face_landmarks = self._extract_face_landmarks(face_results, frame.shape)

        # Detect contacts for all active regions
        contact_data = self._detect_contacts(hand_landmarks, face_landmarks)

        # Apply temporal filtering
        filtered_data = self._apply_temporal_filtering(contact_data)

        # Draw visualizations
        self._draw_hands(annotated_frame, hand_results)
        if face_landmarks is not None:
            self._draw_active_regions(annotated_frame, face_landmarks)
        self._draw_contact_points(annotated_frame, filtered_data)

        # Prepare detection data
        detection_data = {
            "hands_detected": len(hand_landmarks) > 0,
            "face_detected": face_landmarks is not None,
            "contact_points": sum(len(contacts) for contacts in filtered_data.values()),
            "active_regions": list(filtered_data.keys()),
            "alerts_active": [region for region, data in filtered_data.items() if data.get("alert_active", False)],
        }

        return annotated_frame, detection_data

    def _extract_hand_landmarks(self, results, frame_shape) -> List[np.ndarray]:
        """Extract hand landmarks as pixel coordinates"""
        landmarks = []
        if results.multi_hand_landmarks:
            height, width = frame_shape[:2]
            for hand_landmarks in results.multi_hand_landmarks:
                hand_points = []
                for landmark in hand_landmarks.landmark:
                    x = int(landmark.x * width)
                    y = int(landmark.y * height)
                    z = landmark.z
                    hand_points.append([x, y, z])
                landmarks.append(np.array(hand_points))
        return landmarks

    def _extract_face_landmarks(self, results, frame_shape) -> np.ndarray:
        """Extract face landmarks as pixel coordinates"""
        if results.multi_face_landmarks:
            height, width = frame_shape[:2]
            face_landmarks = results.multi_face_landmarks[0]
            face_points = []
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                z = landmark.z
                face_points.append([x, y, z])
            return np.array(face_points)
        return None

    def _detect_contacts(self, hand_landmarks: List[np.ndarray], face_landmarks: np.ndarray) -> Dict[str, List]:
        """Detect contacts for all active regions"""
        if len(hand_landmarks) == 0 or face_landmarks is None:
            return {region: [] for region in Config.ACTIVE_REGIONS}

        # Create region polygons
        regions = self._create_region_polygons(face_landmarks)

        # Detect contacts for each active region
        contact_data = {}
        for region in Config.ACTIVE_REGIONS:
            contact_data[region] = []

            if region in regions:
                region_polygon = regions[region]

                # Check each hand
                for hand in hand_landmarks:
                    for fingertip_idx in self.FINGERTIPS:
                        fingertip = hand[fingertip_idx][:2]

                        # Check distance to region
                        if len(region_polygon) > 2:
                            distance = cv2.pointPolygonTest(region_polygon, tuple(fingertip), True)

                            # Within contact threshold
                            if distance >= -20:  # 20 pixels tolerance
                                contact_data[region].append({"point": fingertip, "fingertip_idx": fingertip_idx, "distance": abs(distance)})

        return contact_data

    def _create_region_polygons(self, face_landmarks: np.ndarray) -> Dict[str, np.ndarray]:
        """Create polygons for all regions"""
        regions = {}

        if "scalp" in Config.ACTIVE_REGIONS:
            regions["scalp"] = self._create_scalp_region(face_landmarks)

        if "eyebrows" in Config.ACTIVE_REGIONS:
            regions["eyebrows"] = self._create_eyebrow_region(face_landmarks)

        if "eyes" in Config.ACTIVE_REGIONS:
            regions["eyes"] = self._create_eye_region(face_landmarks)

        if "mouth" in Config.ACTIVE_REGIONS:
            regions["mouth"] = self._create_mouth_region(face_landmarks)

        if "beard" in Config.ACTIVE_REGIONS:
            regions["beard"] = self._create_beard_region(face_landmarks)

        return regions

    def _create_scalp_region(self, face_landmarks: np.ndarray) -> np.ndarray:
        """Create scalp region above the face"""
        # Get key face boundary points
        forehead_center = face_landmarks[9][:2]
        left_temple = face_landmarks[162][:2]
        right_temple = face_landmarks[389][:2]
        left_forehead = face_landmarks[103][:2]
        right_forehead = face_landmarks[332][:2]

        # Calculate face width and height for scaling
        face_width = np.linalg.norm(left_temple - right_temple)
        scalp_height = face_width * 0.6  # Adjustable parameter

        # Create scalp region above the forehead
        scalp_points = []
        scalp_points.append(left_forehead)
        scalp_points.append(left_temple)

        # Extend upward for scalp area
        left_scalp_top = left_temple + np.array([-face_width * 0.1, -scalp_height])
        right_scalp_top = right_temple + np.array([face_width * 0.1, -scalp_height])
        center_scalp_top = forehead_center + np.array([0, -scalp_height * 1.5])
        scalp_points.extend([left_scalp_top, center_scalp_top, right_scalp_top])
        scalp_points.extend([right_temple, right_forehead])

        return np.array(scalp_points, dtype=np.int32)

    def _create_eyebrow_region(self, face_landmarks: np.ndarray) -> np.ndarray:
        """Create eyebrow region"""
        # Left and right eyebrow landmarks
        eyebrow_indices = [
            70,
            63,
            105,
            66,
            107,
            55,
            65,
            52,
            53,
            46,  # Right eyebrow
            285,
            295,
            282,
            283,
            276,
            300,
            293,
            334,
            296,
            336,
        ]  # Left eyebrow

        eyebrow_points = face_landmarks[eyebrow_indices][:, :2]
        hull = cv2.convexHull(eyebrow_points.astype(np.int32))
        return hull.reshape(-1, 2)

    def _create_eye_region(self, face_landmarks: np.ndarray) -> np.ndarray:
        """Create eye region"""
        # Left and right eye landmarks
        eye_indices = [
            33,
            7,
            163,
            144,
            145,
            153,
            154,
            155,
            133,
            173,
            157,
            158,
            159,
            160,
            161,
            246,  # Right eye
            362,
            398,
            384,
            385,
            386,
            387,
            388,
            466,
            263,
            249,
            390,
            373,
            374,
            380,
            381,
            382,
        ]  # Left eye

        eye_points = face_landmarks[eye_indices][:, :2]
        hull = cv2.convexHull(eye_points.astype(np.int32))
        return hull.reshape(-1, 2)

    def _create_mouth_region(self, face_landmarks: np.ndarray) -> np.ndarray:
        """Create mouth region"""
        # Mouth landmarks
        mouth_indices = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318, 78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308]

        mouth_points = face_landmarks[mouth_indices][:, :2]
        hull = cv2.convexHull(mouth_points.astype(np.int32))
        return hull.reshape(-1, 2)

    def _create_beard_region(self, face_landmarks: np.ndarray) -> np.ndarray:
        """Create facial hair region including cheeks and jawline"""
        # Get key reference points
        mouth_left = face_landmarks[61][:2]  # Left mouth corner
        mouth_right = face_landmarks[291][:2]  # Right mouth corner
        chin_center = face_landmarks[175][:2]  # Bottom chin point

        # Get cheek reference points (approximate cheekbone area)
        left_cheek = face_landmarks[117][:2]  # Left cheek
        right_cheek = face_landmarks[346][:2]  # Right cheek

        # Calculate face center and dimensions
        face_center_x = (mouth_left[0] + mouth_right[0]) / 2
        face_width = np.linalg.norm(left_cheek - right_cheek)

        # Define region boundaries
        # Extend wider to include cheek facial hair
        region_width = face_width * 0.8  # Cover most of lower face width
        region_height = face_width * 0.3  # Height for facial hair coverage

        # Calculate boundaries
        left_x = face_center_x - region_width / 2
        right_x = face_center_x + region_width / 2

        # Top boundary: slightly above mouth level to catch mustache area
        top_y = mouth_left[1] - region_height * 0.3

        # Bottom boundary: extend below chin for beard coverage
        bottom_y = chin_center[1] + region_height * 0.7

        # Create expanded facial hair region (clockwise)
        beard_points = [
            [left_x, top_y],  # Top left (cheek area)
            [right_x, top_y],  # Top right (cheek area)
            [right_x, bottom_y],  # Bottom right (jawline)
            [left_x, bottom_y],  # Bottom left (jawline)
        ]

        return np.array(beard_points, dtype=np.int32)

    def _apply_temporal_filtering(self, contact_data: Dict[str, List]) -> Dict[str, Dict]:
        """Apply temporal filtering for each region"""
        current_time = time.time()
        filtered_data = {}

        for region, contacts in contact_data.items():
            state = self.region_states[region]
            settings = Config.REGION_SETTINGS[region]
            has_contact = len(contacts) > 0

            if has_contact:
                if state["contact_start_time"] is None:
                    state["contact_start_time"] = current_time

                # Check if contact persisted long enough
                duration = current_time - state["contact_start_time"]
                if duration >= settings["min_detection_time"]:
                    state["alert_active"] = True
                else:
                    state["alert_active"] = False
            else:
                # Reset contact tracking
                state["contact_start_time"] = None
                state["alert_active"] = False

            filtered_data[region] = {
                "contacts": contacts,
                "alert_active": state["alert_active"],
                "contact_duration": (current_time - state["contact_start_time"] if state["contact_start_time"] else 0),
            }

        return filtered_data

    def _draw_hands(self, frame: np.ndarray, hand_results):
        """Draw hand landmarks"""
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style(),
                )

    def _draw_active_regions(self, frame: np.ndarray, face_landmarks: np.ndarray):
        """Draw only active region boundaries"""
        regions = self._create_region_polygons(face_landmarks)

        for region_name, region_polygon in regions.items():
            if len(region_polygon) > 2:
                # Draw region boundary
                cv2.polylines(frame, [region_polygon], True, Config.REGION_COLOR, 2)

                # Add region label
                center = np.mean(region_polygon, axis=0).astype(int)
                cv2.putText(frame, region_name.upper(), tuple(center), cv2.FONT_HERSHEY_SIMPLEX, 0.6, Config.REGION_COLOR, 2)

    def _draw_contact_points(self, frame: np.ndarray, filtered_data: Dict[str, Dict]):
        """Draw contact points and alerts"""
        alert_regions = []

        for region, data in filtered_data.items():
            # Draw contact points
            for contact in data["contacts"]:
                point = tuple(contact["point"].astype(int))
                cv2.circle(frame, point, 8, Config.CONTACT_COLOR, -1)
                cv2.circle(frame, point, 12, Config.CONTACT_COLOR, 2)
                cv2.circle(frame, point, 16, (255, 255, 255), 1)

            # Track alert regions
            if data["alert_active"]:
                alert_regions.append(region)

        # Draw alert border if any region has alert
        if alert_regions:
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (0, 0), (w - 1, h - 1), Config.CONTACT_COLOR, 5)

            alert_text = f"CONTACT: {', '.join(alert_regions).upper()}"
            cv2.putText(frame, alert_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, Config.CONTACT_COLOR, 2)

    def toggle_region(self, region: str):
        """Toggle region on/off"""
        if region in Config.AVAILABLE_REGIONS:
            if region in Config.ACTIVE_REGIONS:
                Config.ACTIVE_REGIONS.remove(region)
            else:
                Config.ACTIVE_REGIONS.append(region)

    def cleanup(self):
        """Clean up MediaPipe resources"""
        self.hands.close()
        self.face_mesh.close()
