/**
 * JavaScript MediaPipe Detection System
 * Replaces the Python backend with direct browser-based detection
 */

import { HandLandmarker, FaceLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

class MindfulTouchDetector {
    constructor() {
        this.handLandmarker = null;
        this.faceLandmarker = null;
        this.isInitialized = false;
        
        // Detection state for each region
        this.regionStates = {
            scalp: { contactStartTime: null, alertActive: false, lastAlertTime: 0 },
            eyebrows: { contactStartTime: null, alertActive: false, lastAlertTime: 0 },
            eyes: { contactStartTime: null, alertActive: false, lastAlertTime: 0 },
            mouth: { contactStartTime: null, alertActive: false, lastAlertTime: 0 },
            beard: { contactStartTime: null, alertActive: false, lastAlertTime: 0 }
        };
        
        // Active regions (start with scalp only, like Python config)
        this.activeRegions = ['scalp'];
        
        // Detection configuration
        this.config = {
            handDetectionConfidence: 0.7,
            handTrackingConfidence: 0.7,
            faceDetectionConfidence: 0.7,
            faceTrackingConfidence: 0.7,
            contactThreshold: 20, // 20 pixels tolerance (like Python)
            minDetectionTime: 300, // 0.3 seconds in milliseconds
            alertCooldown: 5000 // 5 seconds cooldown between alerts
        };
        
        // Region-specific settings (converting Python normalized values to pixels)
        // Python uses 0.05 = 5% of image width/height, so for 1280x720:
        // 0.05 * 1280 = 64 pixels for width-based, 0.05 * 720 = 36 pixels for height-based
        // Using average of ~50 pixels for 0.05, scaled proportionally
        this.regionSettings = {
            scalp: { contactThreshold: 64, minDetectionTime: 300 }, // 0.05 * 1280
            eyebrows: { contactThreshold: 26, minDetectionTime: 200 }, // 0.02 * 1280  
            eyes: { contactThreshold: 26, minDetectionTime: 200 }, // 0.02 * 1280
            mouth: { contactThreshold: 38, minDetectionTime: 200 }, // 0.03 * 1280
            beard: { contactThreshold: 51, minDetectionTime: 250 } // 0.04 * 1280
        };
        
        // Face mesh landmark indices for different regions (from Python implementation)
        this.faceRegionIndices = {
            // Scalp: will be computed dynamically above forehead
            scalp: [9, 10, 151, 162, 389, 103, 332], // Key forehead/temple points for scalp calculation
            // Eyebrows: Combined left and right eyebrow landmarks
            eyebrows: [46, 53, 52, 51, 48, 115, 131, 134, 102, 49, 220, 276, 283, 300, 293, 334, 296, 336, 285, 305],
            // Eyes: Combined left and right eye landmarks  
            eyes: [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246, 362, 398, 384, 385, 386, 387, 388, 466, 263, 249, 390, 373, 374, 380, 381, 382],
            // Mouth: Mouth landmark indices
            mouth: [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318, 78, 95, 88, 178, 87, 14, 317, 402],
            // Beard: Lower face/jaw landmarks  
            beard: [175, 199, 200, 3, 51, 48, 115, 131, 134, 102, 49, 220, 305, 285, 336, 296, 334, 293, 300, 276]
        };
        
        // Fingertip landmark indices
        this.fingertips = [4, 8, 12, 16, 20]; // Thumb, Index, Middle, Ring, Pinky
    }
    
    async initialize() {
        try {
            console.log('Initializing MediaPipe detection...');
            
            // Use dynamic import for MediaPipe
            const { HandLandmarker, FaceLandmarker, FilesetResolver } = await import('@mediapipe/tasks-vision');
            
            console.log('MediaPipe objects loaded:', { HandLandmarker: !!HandLandmarker, FaceLandmarker: !!FaceLandmarker, FilesetResolver: !!FilesetResolver });
            
            // Initialize MediaPipe
            const vision = await FilesetResolver.forVisionTasks(
                "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.8/wasm"
            );
            
            // Initialize Hand Landmarker
            this.handLandmarker = await HandLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
                    delegate: "GPU"
                },
                numHands: 2,
                runningMode: "VIDEO",
                minHandDetectionConfidence: this.config.handDetectionConfidence,
                minHandPresenceConfidence: this.config.handTrackingConfidence,
                minTrackingConfidence: this.config.handTrackingConfidence
            });
            
            // Initialize Face Landmarker
            this.faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
                baseOptions: {
                    modelAssetPath: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                    delegate: "GPU"
                },
                numFaces: 1,
                runningMode: "VIDEO",
                minFaceDetectionConfidence: this.config.faceDetectionConfidence,
                minFacePresenceConfidence: this.config.faceTrackingConfidence,
                minTrackingConfidence: this.config.faceTrackingConfidence
            });
            
            this.isInitialized = true;
            console.log('MediaPipe detection initialized successfully!');
            return true;
            
        } catch (error) {
            console.error('Failed to initialize MediaPipe detection:', error);
            this.isInitialized = false;
            return false;
        }
    }
    
    detectFromVideo(video, timestamp) {
        if (!this.isInitialized || !this.handLandmarker || !this.faceLandmarker) {
            console.warn('Detection not initialized');
            return null;
        }
        
        try {
            // Get hand and face landmarks
            const handResults = this.handLandmarker.detectForVideo(video, timestamp);
            const faceResults = this.faceLandmarker.detectForVideo(video, timestamp);
            
            // Debug output occasionally
            if (Math.floor(timestamp) % 2000 < 50) { // Every ~2 seconds
                console.log('Hand results:', handResults.landmarks.length, 'hands detected');
                console.log('Face results:', faceResults.faceLandmarks.length, 'faces detected');
            }
            
            // Process detection results with actual video dimensions
            return this.processDetectionResults(handResults, faceResults, timestamp, video.videoWidth, video.videoHeight);
            
        } catch (error) {
            console.error('Detection error:', error);
            return null;
        }
    }
    
    processDetectionResults(handResults, faceResults, timestamp, videoWidth = 1280, videoHeight = 720) {
        const detectionData = {
            timestamp: timestamp,
            hands_detected: handResults.landmarks.length > 0,
            face_detected: faceResults.faceLandmarks.length > 0,
            contact_points: 0,
            alerts_active: [],
            contacts_active: [], // New: regions with active contact
            regionContacts: {}
        };
        
        // If no hands, face, or no active regions, clear all regions
        if (!detectionData.hands_detected || !detectionData.face_detected || this.activeRegions.length === 0) {
            this.clearAllRegions(timestamp);
            return detectionData;
        }

        // Get face landmarks (assuming single face)
        const faceLandmarks = faceResults.faceLandmarks[0];
        
        // Convert MediaPipe normalized coordinates to pixel coordinates
        const facePixelLandmarks = faceLandmarks.map(landmark => ({
            x: landmark.x * videoWidth,
            y: landmark.y * videoHeight,
            z: landmark.z
        }));

        // Create region polygons
        const regionPolygons = this.createRegionPolygons(facePixelLandmarks, videoWidth, videoHeight);

        // Detect contacts for each active region
        const contactData = {};
        this.activeRegions.forEach(regionName => {
            contactData[regionName] = [];
            
            if (regionPolygons[regionName]) {
                const regionPolygon = regionPolygons[regionName];
                
                // Check each hand against this region
                handResults.landmarks.forEach((handLandmarks, handIndex) => {
                    // Convert hand landmarks to pixel coordinates
                    const handPixelLandmarks = handLandmarks.map(landmark => ({
                        x: landmark.x * videoWidth,
                        y: landmark.y * videoHeight,
                        z: landmark.z
                    }));
                    
                    // Check each fingertip
                    this.fingertips.forEach(fingertipIndex => {
                        const fingertip = handPixelLandmarks[fingertipIndex];
                        
                        // Calculate distance to region polygon
                        const distance = this.pointPolygonDistance(fingertip, regionPolygon);
                        
                        // Get dynamic threshold based on video dimensions (like Python normalized coordinates)
                        const pythonThreshold = {
                            scalp: 0.05, eyebrows: 0.02, eyes: 0.02, mouth: 0.03, beard: 0.04
                        }[regionName] || 0.05;
                        const threshold = pythonThreshold * videoWidth; // Convert to pixels
                        
                        // Within contact threshold
                        if (distance <= threshold) {
                            contactData[regionName].push({
                                point: fingertip,
                                fingertipIndex: fingertipIndex,
                                distance: distance
                            });
                        }
                    });
                });
            }
        });

        // Apply temporal filtering and update detection data
        const filteredData = this.applyTemporalFiltering(contactData, timestamp, this.config.alertDelayMs || 0);
        
        // Update detection data
        detectionData.contact_points = Object.values(contactData).reduce((sum, contacts) => sum + contacts.length, 0);
        detectionData.alerts_active = Object.keys(filteredData).filter(region => filteredData[region].alertActive);
        detectionData.contacts_active = Object.keys(contactData).filter(region => contactData[region].length > 0);
        detectionData.regionContacts = contactData;
        
        return detectionData;
    }
    
    clearAllRegions(timestamp) {
        // Clear contact states for all regions
        Object.keys(this.regionStates).forEach(regionName => {
            this.regionStates[regionName].contactStartTime = null;
            this.regionStates[regionName].alertActive = false;
        });
    }
    
    toggleRegion(regionName, enabled) {
        if (enabled && !this.activeRegions.includes(regionName)) {
            this.activeRegions.push(regionName);
        } else if (!enabled) {
            const index = this.activeRegions.indexOf(regionName);
            if (index > -1) {
                this.activeRegions.splice(index, 1);
            }
        }
        
        // Clear state for disabled regions
        if (!enabled && this.regionStates[regionName]) {
            this.regionStates[regionName].contactStartTime = null;
            this.regionStates[regionName].alertActive = false;
        }
    }
    
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    
    // Update alert delay setting from UI
    updateAlertDelay(delaySeconds) {
        this.config.alertDelayMs = delaySeconds * 1000;
    }
    
    destroy() {
        if (this.handLandmarker) {
            this.handLandmarker.close();
            this.handLandmarker = null;
        }
        
        if (this.faceLandmarker) {
            this.faceLandmarker.close();
            this.faceLandmarker = null;
        }
        
        this.isInitialized = false;
    }
    
    createRegionPolygons(faceLandmarks, videoWidth, videoHeight) {
        const regions = {};
        
        this.activeRegions.forEach(regionName => {
            switch(regionName) {
                case 'scalp':
                    regions[regionName] = this.createScalpRegion(faceLandmarks, videoWidth, videoHeight);
                    break;
                case 'eyebrows':
                    regions[regionName] = this.createEyebrowRegion(faceLandmarks);
                    break;
                case 'eyes':
                    regions[regionName] = this.createEyeRegion(faceLandmarks);
                    break;
                case 'mouth':
                    regions[regionName] = this.createMouthRegion(faceLandmarks);
                    break;
                case 'beard':
                    regions[regionName] = this.createBeardRegion(faceLandmarks, videoWidth);
                    break;
            }
        });
        
        return regions;
    }
    
    createScalpRegion(faceLandmarks, videoWidth, videoHeight) {
        // Get key face boundary points (like Python implementation)
        const foreheadCenter = faceLandmarks[9];
        const leftTemple = faceLandmarks[162];
        const rightTemple = faceLandmarks[389];
        const leftForehead = faceLandmarks[103];
        const rightForehead = faceLandmarks[332];
        
        // Calculate face width and height for scaling
        const faceWidth = Math.sqrt(Math.pow(leftTemple.x - rightTemple.x, 2) + Math.pow(leftTemple.y - rightTemple.y, 2));
        const scalpHeight = faceWidth * 0.6;
        
        // Create scalp region above the forehead
        const scalpPoints = [];
        scalpPoints.push(leftForehead);
        scalpPoints.push(leftTemple);
        
        // Extend upward for scalp area
        const leftScalpTop = { x: leftTemple.x - faceWidth * 0.1, y: leftTemple.y - scalpHeight };
        const rightScalpTop = { x: rightTemple.x + faceWidth * 0.1, y: rightTemple.y - scalpHeight };
        const centerScalpTop = { x: foreheadCenter.x, y: foreheadCenter.y - scalpHeight * 1.5 };
        
        scalpPoints.push(leftScalpTop, centerScalpTop, rightScalpTop);
        scalpPoints.push(rightTemple, rightForehead);
        
        return scalpPoints;
    }
    
    createEyebrowRegion(faceLandmarks) {
        const eyebrowIndices = this.faceRegionIndices.eyebrows;
        return eyebrowIndices.map(index => faceLandmarks[index]);
    }
    
    createEyeRegion(faceLandmarks) {
        const eyeIndices = this.faceRegionIndices.eyes;
        return eyeIndices.map(index => faceLandmarks[index]);
    }
    
    createMouthRegion(faceLandmarks) {
        const mouthIndices = this.faceRegionIndices.mouth;
        return mouthIndices.map(index => faceLandmarks[index]);
    }
    
    createBeardRegion(faceLandmarks, videoWidth) {
        // Get key reference points (like Python implementation)
        const mouthLeft = faceLandmarks[61];
        const mouthRight = faceLandmarks[291];
        const chinCenter = faceLandmarks[175];
        const leftCheek = faceLandmarks[117];
        const rightCheek = faceLandmarks[346];
        
        // Calculate face center and dimensions
        const faceCenterX = (mouthLeft.x + mouthRight.x) / 2;
        const faceWidth = Math.sqrt(Math.pow(leftCheek.x - rightCheek.x, 2) + Math.pow(leftCheek.y - rightCheek.y, 2));
        
        // Define region boundaries
        const regionWidth = faceWidth * 0.8;
        const regionHeight = faceWidth * 0.3;
        
        // Calculate boundaries
        const leftX = faceCenterX - regionWidth / 2;
        const rightX = faceCenterX + regionWidth / 2;
        const topY = mouthLeft.y; // Start from mouth level
        const bottomY = chinCenter.y + regionHeight;
        
        return [
            { x: leftX, y: topY },
            { x: rightX, y: topY },
            { x: rightX, y: bottomY },
            { x: leftX, y: bottomY }
        ];
    }
    
    // Point-in-polygon test with distance calculation (like Python cv2.pointPolygonTest)
    pointPolygonDistance(point, polygon) {
        if (!polygon || polygon.length < 3) return Infinity;
        
        // First check if point is inside polygon
        let inside = false;
        let j = polygon.length - 1;
        
        for (let i = 0; i < polygon.length; j = i++) {
            if (((polygon[i].y > point.y) !== (polygon[j].y > point.y)) &&
                (point.x < (polygon[j].x - polygon[i].x) * (point.y - polygon[i].y) / (polygon[j].y - polygon[i].y) + polygon[i].x)) {
                inside = !inside;
            }
        }
        
        // If inside, return 0 (contact detected)
        if (inside) return 0;
        
        // If outside, calculate minimum distance to polygon edges
        let minDistance = Infinity;
        for (let i = 0; i < polygon.length; i++) {
            const j = (i + 1) % polygon.length;
            const distance = this.pointToLineDistance(point, polygon[i], polygon[j]);
            minDistance = Math.min(minDistance, distance);
        }
        
        return minDistance;
    }
    
    pointToLineDistance(point, lineStart, lineEnd) {
        const A = point.x - lineStart.x;
        const B = point.y - lineStart.y;
        const C = lineEnd.x - lineStart.x;
        const D = lineEnd.y - lineStart.y;
        
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        
        if (lenSq === 0) {
            // Line is actually a point
            return Math.sqrt(A * A + B * B);
        }
        
        let param = dot / lenSq;
        param = Math.max(0, Math.min(1, param)); // Clamp to line segment
        
        const xx = lineStart.x + param * C;
        const yy = lineStart.y + param * D;
        
        const dx = point.x - xx;
        const dy = point.y - yy;
        
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    applyTemporalFiltering(contactData, timestamp, alertDelayMs = 0) {
        const filteredData = {};
        
        Object.keys(contactData).forEach(regionName => {
            const contacts = contactData[regionName];
            const regionState = this.regionStates[regionName];
            const settings = this.regionSettings[regionName];
            const hasContact = contacts.length > 0;
            
            // Use alert delay as minimum detection time if set, otherwise use region-specific timing
            const minDetectionTime = alertDelayMs > 0 ? alertDelayMs : settings.minDetectionTime;
            
            if (hasContact) {
                if (regionState.contactStartTime === null) {
                    regionState.contactStartTime = timestamp;
                }
                
                // Check if contact persisted long enough
                const duration = timestamp - regionState.contactStartTime;
                if (duration >= minDetectionTime) {
                    regionState.alertActive = true;
                } else {
                    regionState.alertActive = false;
                }
            } else {
                // Reset contact tracking
                regionState.contactStartTime = null;
                regionState.alertActive = false;
            }
            
            filteredData[regionName] = {
                contacts: contacts,
                alertActive: regionState.alertActive,
                contactDuration: regionState.contactStartTime ? timestamp - regionState.contactStartTime : 0
            };
        });
        
        return filteredData;
    }
}

export { MindfulTouchDetector };
