"""Detection worker thread for camera processing."""

import time
import threading
from typing import Dict, List, Optional

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal

from backend.detection.multi_region_detector import MultiRegionDetector


class DetectionWorker(QThread):
    """Worker thread for running detection in background."""
    
    # Signals
    detection_data = pyqtSignal(dict)  # Emits detection results
    frame_ready = pyqtSignal(np.ndarray)  # Emits camera frames
    error_occurred = pyqtSignal(str)  # Emits error messages
    
    def __init__(self):
        super().__init__()
        self.detector = None
        self.cap = None
        self.enabled_regions = ['Scalp']  # Default enabled regions
        self.is_running = False
        self.should_stop = False
        
        # Alert management
        self.last_alert_time = {}  # Track last alert time per region
        self.alert_delay = 3  # seconds between alerts
        
        # Performance settings
        self.frame_skip = 2  # Process every 2nd frame for better performance
        
    def set_enabled_regions(self, regions: List[str]):
        """Update enabled detection regions."""
        self.enabled_regions = regions
        
        # Map UI region names to detector region names
        region_mapping = {
            'Scalp': 'scalp',
            'Eyebrows': 'eyebrows', 
            'Eyes': 'eyes',
            'Mouth': 'mouth',
            'Beard': 'beard'
        }
        
        # Update Config.ACTIVE_REGIONS
        from backend.detection.config import Config
        Config.ACTIVE_REGIONS = [
            region_mapping[ui_name] for ui_name in regions 
            if ui_name in region_mapping
        ]
        
        print(f"Active regions updated: {Config.ACTIVE_REGIONS}")
                    
    def set_alert_delay(self, delay_seconds: int):
        """Set delay between alerts."""
        self.alert_delay = delay_seconds
        
    def initialize_detector(self):
        """Initialize detector and MediaPipe models once at startup."""
        try:
            print("Initializing detection models...")
            self.detector = MultiRegionDetector()
            print("Detection models initialized successfully")
        except Exception as e:
            print(f"Failed to initialize detection models: {e}")
            
    def start_detection(self):
        """Start the detection process."""
        if not self.is_running:
            self.should_stop = False
            self.start()
            
    def stop_detection(self):
        """Stop the detection process."""
        self.should_stop = True
        if self.is_running:
            self.wait(5000)  # Wait up to 5 seconds for thread to finish
            
    def run(self):
        """Main detection loop running in separate thread."""
        self.is_running = True
        
        try:
            # Initialize camera (detector already initialized at startup)
            from backend.detection.camera_utils import initialize_camera, MockCamera
            from backend.detection.config import Config
            
            if not self.detector:
                print("Detector not initialized, initializing now...")
                self.detector = MultiRegionDetector()
            
            # Try to initialize camera
            self.cap = initialize_camera(
                camera_index=0, 
                width=Config.CAMERA_WIDTH, 
                height=Config.CAMERA_HEIGHT
            )
            
            if self.cap is None:
                print("Could not open camera, falling back to mock camera")
                self.cap = MockCamera(Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)
            
            # Configure enabled regions
            self.set_enabled_regions(self.enabled_regions)
            
            print("Detection worker started")
            
            frame_count = 0
            while not self.should_stop:
                try:
                    # Capture frame
                    ret, frame = self.cap.read()
                    if not ret:
                        print("Failed to read frame from camera")
                        time.sleep(0.1)
                        continue
                    
                    # Always emit frame for display
                    self.frame_ready.emit(frame.copy())
                    
                    # Skip processing some frames for performance
                    frame_count += 1
                    if frame_count % self.frame_skip == 0:
                        # Process frame for detection
                        processed_frame, detection_results = self.detector.process_frame(frame)
                        
                        # Process detection results
                        self.process_detection_results(detection_results)
                    
                    # Control frame rate (~15 FPS for processing, 30 FPS for display)
                    time.sleep(1/30)
                    
                except Exception as e:
                    print(f"Error in detection loop: {e}")
                    self.error_occurred.emit(str(e))
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Failed to initialize detector: {e}")
            self.error_occurred.emit(f"Camera initialization failed: {e}")
        finally:
            if hasattr(self, 'cap') and self.cap:
                self.cap.release()
            self.is_running = False
            print("Detection worker stopped")
            
    def process_detection_results(self, results: Dict):
        """Process detection results and emit appropriate signals."""
        if not results:
            return
            
        # Extract basic detection info
        hands_detected = results.get('hands_detected', False)
        face_detected = results.get('face_detected', False)
        contact_points_count = results.get('contact_points', 0)
        alerts_active = results.get('alerts_active', [])
        
        # Map detector region names back to UI names
        region_mapping = {
            'scalp': 'Scalp',
            'eyebrows': 'Eyebrows',
            'eyes': 'Eyes', 
            'mouth': 'Mouth',
            'beard': 'Beard'
        }
        
        # Determine which regions have contacts with alert delay
        alert_regions = []
        current_time = time.time()
        
        # Only trigger alerts if there are actually active alerts from the detector
        if alerts_active:
            for detector_region in alerts_active:
                ui_region = region_mapping.get(detector_region, detector_region)
                
                # Check if enough time has passed since last alert for this region
                if (ui_region not in self.last_alert_time or 
                    current_time - self.last_alert_time[ui_region] >= self.alert_delay):
                    
                    alert_regions.append(ui_region)
                    self.last_alert_time[ui_region] = current_time
                    break  # Only one alert at a time to prevent double sounds
        
        # Prepare detection data
        detection_data = {
            'hands_detected': hands_detected,
            'face_detected': face_detected,
            'contact_points': [{'count': contact_points_count}],  # Format for overlay
            'alert_regions': alert_regions,
            'timestamp': current_time
        }
        
        # Emit detection data
        self.detection_data.emit(detection_data)