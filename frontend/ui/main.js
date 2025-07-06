// Mindful Touch - Frontend JavaScript with MediaPipe Detection
import { MindfulTouchDetector } from './detection.js';
import { CameraManager } from './camera.js';

// Check if Tauri is available (Tauri v2 format)
let invoke;
if (window.__TAURI__ && window.__TAURI__.core) {
    invoke = window.__TAURI__.core.invoke;
} else if (window.__TAURI__ && window.__TAURI__.tauri) {
    invoke = window.__TAURI__.tauri.invoke;
} else {
    // Fallback function for testing
    invoke = async (cmd, args) => {
        return `Mock response for ${cmd}`;
    };
}

class MindfulTouchApp {
    constructor() {
        this.isDetectionRunning = false;
        this.sessionStartTime = null;
        this.statistics = {
            totalDetections: 0, // Only count actual alerts (after delay)
            sessionDuration: 0,
            mindfulStops: 0 // Count when user stops touching before alert
        };
        
        // Notification settings
        this.notificationSettings = {
            enabled: true,
            soundEnabled: true,
            delaySeconds: 3,
            selectedSound: 'chime'
        };
        
        // Alert delay management
        this.alertDelayTimeouts = new Map(); // Track active delays by region
        this.activeAlerts = new Set(); // Track which regions are currently alerting
        
        // Audio context for playing sounds
        this.audioContext = null;
        this.soundBuffers = {};
        
        // Detection system components
        this.detector = new MindfulTouchDetector();
        this.cameraManager = new CameraManager();
        this.isInitialized = false;
        
        // Frame processing
        this.lastFrameTime = 0;
        this.frameCount = 0;
        
        this.init();
    }

    async init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize UI
        this.updateUI();
        
        // Initialize detection system
        await this.initializeDetectionSystem();
        
        // Wait a bit for Tauri to initialize
        setTimeout(async () => {
            await this.testTauriConnection();
        }, 500);
    }

    async initializeDetectionSystem() {
        try {
            console.log('Initializing detection system...');
            
            // Initialize MediaPipe detector only (not camera yet)
            const detectorReady = await this.detector.initialize();
            if (!detectorReady) {
                throw new Error('Failed to initialize MediaPipe detector');
            }
            
            // Set initial alert delay
            this.detector.updateAlertDelay(this.notificationSettings.delaySeconds);
            
            this.isInitialized = true;
            this.updateConnectionStatus(true);
            console.log('Detection system initialized successfully!');
            
        } catch (error) {
            console.error('Failed to initialize detection system:', error);
            this.showError(`Detection system initialization failed: ${error.message}`);
            this.updateConnectionStatus(false);
        }
    }

    async startDetection() {
        if (!this.isInitialized) {
            this.showError('Detection system not initialized. Please wait and try again.');
            return;
        }

        try {
            // Initialize camera now (when user clicks start)
            console.log('Initializing camera...');
            const cameraReady = await this.cameraManager.initialize();
            if (!cameraReady) {
                throw new Error('Failed to initialize camera');
            }
            
            this.isDetectionRunning = true;
            this.sessionStartTime = Date.now();
            
            // Update UI first to show camera feed
            this.updateCameraDisplay();
            
            // Start frame processing
            this.cameraManager.startCapture((video, timestamp) => {
                this.processFrame(video, timestamp);
            });
            
            console.log('Detection started');
            
        } catch (error) {
            console.error('Failed to start detection:', error);
            this.showError(`Failed to start detection: ${error.message}`);
            this.isDetectionRunning = false;
        }
    }

    stopDetection() {
        this.isDetectionRunning = false;
        this.sessionStartTime = null;
        
        // Stop camera processing and destroy camera
        if (this.cameraManager) {
            this.cameraManager.stopCapture();
            this.cameraManager.destroy(); // This stops the camera light
        }
        
        // Clear all active alerts and timeouts
        this.alertDelayTimeouts.forEach(timeout => clearTimeout(timeout));
        this.alertDelayTimeouts.clear();
        this.activeAlerts.clear();
        
        // Reset camera display
        this.resetCameraDisplay();
        
        console.log('Detection stopped');
    }

    processFrame(video, timestamp) {
        if (!this.isDetectionRunning || !this.detector.isInitialized) {
            return;
        }

        try {
            // Update frame count for debugging
            this.frameCount++;
            const frameCountElement = document.getElementById('frame-count');
            if (frameCountElement && this.frameCount % 30 === 0) { // Update every 30 frames
                frameCountElement.textContent = this.frameCount;
            }
            
            // Perform detection on current frame
            const detectionResult = this.detector.detectFromVideo(video, timestamp);
            
            if (detectionResult) {
                // Debug detection results
                if (this.frameCount % 60 === 0) { // Log every 60 frames (about once per second)
                    console.log('Detection result:', detectionResult);
                }
                this.onDetectionData(detectionResult);
            }
            
            this.lastFrameTime = timestamp;
            
        } catch (error) {
            console.error('Frame processing error:', error);
        }
    }

    async testTauriConnection() {
        try {
            await invoke('greet', { name: 'Mindful Touch' });
        } catch (error) {
            // Tauri connection test failed - ignore for now
        }
    }

    setupEventListeners() {
        // Start Detection Button
        const startButton = document.getElementById('start-detection');
        startButton.addEventListener('click', () => this.toggleDetection());

        // Region Toggle Switches - initialize to match default detector state
        const regions = ['scalp', 'eyebrows', 'eyes', 'mouth', 'beard'];
        regions.forEach(region => {
            const toggle = document.getElementById(`${region}-toggle`);
            
            // Set initial state to match detector default (only scalp active)
            const isActiveByDefault = this.detector.activeRegions.includes(region);
            toggle.checked = isActiveByDefault;
            
            toggle.addEventListener('change', (e) => this.toggleRegion(region, e.target.checked));
        });
        
        // Notification Settings
        this.setupNotificationListeners();

        // Session timer
        setInterval(() => this.updateSessionTimer(), 1000);
    }

    async toggleDetection() {
        const button = document.getElementById('start-detection');
        
        if (!this.isDetectionRunning) {
            try {
                if (button) {
                    button.textContent = 'Starting...';
                    button.disabled = true;
                }
                
                // Start detection
                await this.startDetection();
                
                if (button) {
                    button.textContent = 'Stop Detection';
                    button.disabled = false;
                }
                
            } catch (error) {
                if (button) {
                    button.textContent = 'Start Detection';
                    button.disabled = false;
                }
                this.showError(`Failed to start detection: ${error.message || error}`);
            }
        } else {
            this.stopDetection();
            if (button) {
                button.textContent = 'Start Detection';
                button.disabled = false;
            }
        }
    }

    async toggleRegion(region, enabled) {
        try {
            // Update the detector's active regions
            if (this.detector) {
                this.detector.toggleRegion(region, enabled);
                console.log(`Region ${region} ${enabled ? 'enabled' : 'disabled'}. Active regions:`, this.detector.activeRegions);
                
                // If no regions are active and detection is running, show warning
                if (this.detector.activeRegions.length === 0 && this.isDetectionRunning) {
                    console.warn('No regions active - detection disabled until at least one region is enabled');
                }
                
                // Clear any active alerts for this region when disabled
                if (!enabled) {
                    if (this.alertDelayTimeouts.has(region)) {
                        clearTimeout(this.alertDelayTimeouts.get(region));
                        this.alertDelayTimeouts.delete(region);
                    }
                    this.activeAlerts.delete(region);
                }
            }
            
            // Update UI to reflect change immediately
            const label = document.querySelector(`#${region}-toggle`).parentElement.querySelector('.region-label');
            if (label) {
                label.style.fontWeight = enabled ? '600' : '500';
                label.style.color = enabled ? '#667eea' : '#4a5568';
            }
            
        } catch (error) {
            console.error('Error toggling region:', error);
        }
    }

    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connection-status');
        if (isConnected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-indicator online';
        } else {
            statusElement.textContent = 'Offline';
            statusElement.className = 'status-indicator offline';
        }
    }

    updateCameraDisplay() {
        const placeholder = document.getElementById('camera-placeholder');
        const cameraFeed = document.getElementById('camera-feed');
        
        console.log('Updating camera display...');
        console.log('Camera manager video:', this.cameraManager.video);
        
        // Hide placeholder and show camera feed
        placeholder.style.display = 'none';
        cameraFeed.style.display = 'block';
        
        // Clear any existing content
        cameraFeed.innerHTML = '';
        
        // Add the camera video element to the DOM
        if (this.cameraManager.video) {
            const video = this.cameraManager.video;
            video.id = 'camera-video';
            video.style.cssText = `
                width: 100%;
                height: 100%;
                object-fit: cover;
                border-radius: 12px;
                background: black;
            `;
            
            console.log('Adding video element to DOM:', video);
            console.log('Video dimensions:', video.videoWidth, 'x', video.videoHeight);
            console.log('Video ready state:', video.readyState);
            console.log('Video src object:', video.srcObject);
            
            cameraFeed.appendChild(video);
            
            // Force video to play if it's not playing
            if (video.paused) {
                video.play().catch(console.error);
            }
        } else {
            console.error('No video element available from camera manager');
        }
        
        // Add detection status overlay
        const overlay = document.createElement('div');
        overlay.id = 'detection-overlay';
        overlay.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 12px;
            z-index: 10;
            min-width: 220px;
            width: 220px;
            box-sizing: border-box;
        `;
        overlay.innerHTML = `
            <div class="detection-status">
                <div class="status-item">
                    <span class="status-label">Hands:</span>
                    <span class="status-value" id="hands-status">Detecting...</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Face:</span>
                    <span class="status-value" id="face-status">Detecting...</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Frames:</span>
                    <span class="status-value" id="frame-count">0</span>
                </div>
            </div>
        `;
        
        // Create stop button
        const stopButton = document.createElement('button');
        stopButton.id = 'stop-detection-btn';
        stopButton.className = 'primary-button';
        stopButton.textContent = 'Stop Detection';
        stopButton.style.cssText = `
            margin-top: 10px;
            background: #ef4444;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            width: 100%;
            box-sizing: border-box;
        `;
        
        stopButton.addEventListener('click', () => {
            this.toggleDetection();
        });
        
        overlay.appendChild(stopButton);
        cameraFeed.appendChild(overlay);
        
        // Ensure camera feed container has relative positioning
        cameraFeed.style.position = 'relative';
        
        console.log('Camera display updated');
    }

    resetCameraDisplay() {
        const placeholder = document.getElementById('camera-placeholder');
        const cameraFeed = document.getElementById('camera-feed');
        
        // Show placeholder and hide camera feed
        placeholder.style.display = 'block';
        cameraFeed.style.display = 'none';
        
        // Clear camera feed content
        cameraFeed.innerHTML = '';
        
        // Reset placeholder content
        placeholder.innerHTML = `
            <div class="camera-icon">📹</div>
            <p>Camera feed will appear here</p>
            <button id="start-detection" class="primary-button" style="width: 140px; text-align: center;">Start Detection</button>
        `;
        
        // Re-attach event listener to the new button
        const button = document.getElementById('start-detection');
        if (button) {
            button.addEventListener('click', () => this.toggleDetection());
        }
    }

    updateSessionTimer() {
        if (this.sessionStartTime) {
            const elapsed = Math.floor((Date.now() - this.sessionStartTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            document.getElementById('session-duration').textContent = 
                `${minutes}m ${seconds}s`;
        }
    }

    updateUI() {
        // Update statistics display
        document.getElementById('total-detections').textContent = this.statistics.totalDetections;
        document.getElementById('mindful-saves').textContent = this.statistics.mindfulStops;
    }

    showError(message) {
        // Create a simple error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1000;
        `;
        
        document.body.appendChild(errorDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            document.body.removeChild(errorDiv);
        }, 5000);
    }

    // Method to receive detection data from WebSocket
    onDetectionData(data) {
        // Handle alert delays - start timers for new alerts, cancel for stopped alerts
        if (data.alerts_active && data.alerts_active.length > 0) {
            // Handle alert delay logic (statistics updated in triggerAlert)
            this.handleAlertDelays(data.alerts_active);
        } else {
            // No alerts active - cancel all pending delays and count mindful stops
            this.handleStoppedTouches();
        }
        
        // Update live status display
        if (this.isDetectionRunning) {
            const handsStatus = document.getElementById('hands-status');
            const faceStatus = document.getElementById('face-status');
            
            if (handsStatus) {
                // Use fixed-width text to prevent box resizing
                handsStatus.textContent = data.hands_detected ? 'Detected ✓' : 'Not detected ✗';
                handsStatus.style.color = data.hands_detected ? '#10b981' : '#ef4444';
                handsStatus.style.display = 'inline-block';
                handsStatus.style.width = '120px';
                handsStatus.style.whiteSpace = 'nowrap';
            }
            
            if (faceStatus) {
                // Use fixed-width text to prevent box resizing
                faceStatus.textContent = data.face_detected ? 'Detected ✓' : 'Not detected ✗';
                faceStatus.style.color = data.face_detected ? '#10b981' : '#ef4444';
                faceStatus.style.display = 'inline-block';
                faceStatus.style.width = '120px';
                faceStatus.style.whiteSpace = 'nowrap';
            }
            
            // Update detection overlay with contact and alert information
            const overlay = document.getElementById('detection-overlay');
            if (overlay) {
                this.updateDetectionOverlay(overlay, data);
            }
        }
        
        this.updateUI();
    }
    
    updateDetectionOverlay(overlay, data) {
        // Add contact points and alert information to overlay
        const contactInfo = overlay.querySelector('.contact-info') || document.createElement('div');
        contactInfo.className = 'contact-info';
        contactInfo.style.cssText = 'margin-top: 8px; font-size: 11px;';
        
        const alertsActive = data.alerts_active || [];
        const contactsActive = data.contacts_active || [];
        
        // Show which regions have contact vs which are alerting
        const statusLines = [];
        if (contactsActive.length > 0) {
            statusLines.push(`<div style="color: #f59e0b;">Contact: ${contactsActive.join(', ')}</div>`);
        }
        if (alertsActive.length > 0) {
            statusLines.push(`<div style="color: #ef4444; font-weight: bold;">⚠️ Alert: ${alertsActive.join(', ')}</div>`);
        }
        if (contactsActive.length === 0 && alertsActive.length === 0) {
            statusLines.push('<div style="color: #10b981;">No contact detected</div>');
        }
        
        contactInfo.innerHTML = statusLines.join('');
        
        if (!overlay.querySelector('.contact-info')) {
            overlay.appendChild(contactInfo);
        }
        
        // Visual flash is now handled by triggerOverlayFlash() method
    }
    
    // Notification settings event listeners
    setupNotificationListeners() {
        // Notification enabled toggle
        const notificationToggle = document.getElementById('notifications-enabled');
        notificationToggle.addEventListener('change', (e) => {
            this.notificationSettings.enabled = e.target.checked;
        });
        
        // Sound enabled toggle
        const soundToggle = document.getElementById('sound-enabled');
        soundToggle.addEventListener('change', (e) => {
            this.notificationSettings.soundEnabled = e.target.checked;
        });
        
        // Delay slider
        const delaySlider = document.getElementById('notification-delay');
        const delayValue = document.getElementById('delay-value');
        delaySlider.addEventListener('input', (e) => {
            this.notificationSettings.delaySeconds = parseInt(e.target.value);
            delayValue.textContent = `${e.target.value}s`;
            
            // Update detector with new alert delay
            if (this.detector) {
                this.detector.updateAlertDelay(this.notificationSettings.delaySeconds);
            }
        });
        
        // Sound selection buttons
        const soundSelectButtons = document.querySelectorAll('.sound-select-button');
        soundSelectButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Remove active class from all buttons
                soundSelectButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                // Update selected sound
                this.notificationSettings.selectedSound = e.target.dataset.sound;
            });
        });
        
        // Test sound button
        const testButton = document.getElementById('test-sound-btn');
        testButton.addEventListener('click', () => {
            this.playTestSound(this.notificationSettings.selectedSound);
        });
        
        // Initialize audio context
        this.initializeAudio();
    }
    
    // Initialize audio context and create sound buffers
    async initializeAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create different sound frequencies for testing
            await this.createSoundBuffers();
            
            // Add one-time user interaction listener to unlock audio
            this.addAudioUnlockListener();
        } catch (error) {
            console.warn('Audio initialization failed:', error);
        }
    }
    
    // Add listener to unlock audio on first user interaction
    addAudioUnlockListener() {
        const unlockAudio = async () => {
            if (this.audioContext && this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
                console.log('Audio context unlocked via user interaction');
            }
            // Remove listener after first use
            document.removeEventListener('click', unlockAudio);
            document.removeEventListener('keydown', unlockAudio);
        };
        
        document.addEventListener('click', unlockAudio, { once: true });
        document.addEventListener('keydown', unlockAudio, { once: true });
    }
    
    // Create sound buffers for different notification sounds
    async createSoundBuffers() {
        const sampleRate = this.audioContext.sampleRate;
        
        // Chime sound (multiple frequencies)
        const chimeBuffer = this.audioContext.createBuffer(1, sampleRate * 0.5, sampleRate);
        const chimeData = chimeBuffer.getChannelData(0);
        for (let i = 0; i < chimeData.length; i++) {
            const t = i / sampleRate;
            chimeData[i] = Math.sin(2 * Math.PI * 800 * t) * Math.exp(-t * 3) * 0.3 +
                          Math.sin(2 * Math.PI * 1200 * t) * Math.exp(-t * 4) * 0.2;
        }
        this.soundBuffers.chime = chimeBuffer;
        
        // Beep sound (single frequency)
        const beepBuffer = this.audioContext.createBuffer(1, sampleRate * 0.3, sampleRate);
        const beepData = beepBuffer.getChannelData(0);
        for (let i = 0; i < beepData.length; i++) {
            const t = i / sampleRate;
            beepData[i] = Math.sin(2 * Math.PI * 600 * t) * 0.3;
        }
        this.soundBuffers.beep = beepBuffer;
        
        // Gentle sound (soft sine wave)
        const gentleBuffer = this.audioContext.createBuffer(1, sampleRate * 0.8, sampleRate);
        const gentleData = gentleBuffer.getChannelData(0);
        for (let i = 0; i < gentleData.length; i++) {
            const t = i / sampleRate;
            gentleData[i] = Math.sin(2 * Math.PI * 440 * t) * Math.exp(-t * 2) * 0.2 +
                           Math.sin(2 * Math.PI * 880 * t) * Math.exp(-t * 3) * 0.1;
        }
        this.soundBuffers.gentle = gentleBuffer;
    }
    
    // Play test sound
    async playTestSound(soundType) {
        if (!this.audioContext || !this.soundBuffers[soundType]) return;
        
        try {
            // Resume audio context if suspended (standard browser behavior)
            if (this.audioContext.state === 'suspended') {
                await this.audioContext.resume();
            }
            
            const source = this.audioContext.createBufferSource();
            source.buffer = this.soundBuffers[soundType];
            source.connect(this.audioContext.destination);
            source.start();
            source.onended = () => source.disconnect();
            
        } catch (error) {
            console.error('Error playing sound:', error);
        }
    }
    
    // Handle alert delays - start timers for new regions, maintain existing ones
    handleAlertDelays(alertRegions) {
        // Use alert delay as the minimum contact duration (overrides region-specific timing)
        const alertDelayMs = this.notificationSettings.delaySeconds * 1000;
        
        alertRegions.forEach(region => {
            // If this region is not already in delay or alerting, start delay timer
            if (!this.alertDelayTimeouts.has(region) && !this.activeAlerts.has(region)) {
                
                if (alertDelayMs === 0) {
                    // No delay - trigger immediately
                    this.triggerAlert([region]);
                } else {
                    // Start delay timer - contact must persist for the full alert delay duration
                    const timeoutId = setTimeout(() => {
                        this.alertDelayTimeouts.delete(region);
                        this.triggerAlert([region]);
                    }, alertDelayMs);
                    
                    this.alertDelayTimeouts.set(region, timeoutId);
                }
            }
        });
        
        // Cancel delays for regions that are no longer active (contact broken)
        for (const [region, timeoutId] of this.alertDelayTimeouts.entries()) {
            if (!alertRegions.includes(region)) {
                clearTimeout(timeoutId);
                this.alertDelayTimeouts.delete(region);
            }
        }
        
        // Remove from active alerts if no longer detected
        for (const region of this.activeAlerts) {
            if (!alertRegions.includes(region)) {
                this.activeAlerts.delete(region);
            }
        }
    }
    
    // Cancel all alert delays
    cancelAllAlertDelays() {
        // Clear all timeout timers
        for (const [region, timeoutId] of this.alertDelayTimeouts.entries()) {
            clearTimeout(timeoutId);
        }
        this.alertDelayTimeouts.clear();
        this.activeAlerts.clear();
    }
    
    // Handle stopped touches (positive reinforcement)
    handleStoppedTouches() {
        // Count mindful stops only if there were pending delays
        if (this.alertDelayTimeouts.size > 0) {
            this.statistics.mindfulStops++;
            
            // Show positive notification
            if (this.notificationSettings.enabled) {
                this.showPositiveNotification();
            }
        }
        
        // Cancel all pending delays
        this.cancelAllAlertDelays();
    }
    
    // Trigger the actual alert (after delay)
    triggerAlert(alertRegions) {
        // Add to active alerts
        alertRegions.forEach(region => this.activeAlerts.add(region));
        
        // Count as actual detection (only when alert actually fires)
        this.statistics.totalDetections++;
        
        // Show visual notification if enabled
        if (this.notificationSettings.enabled) {
            this.showNotification(alertRegions);
        }
        
        // Play sound if enabled (independent of visual notifications)
        if (this.notificationSettings.soundEnabled) {
            this.playTestSound(this.notificationSettings.selectedSound);
        }
        
        // Always trigger visual flash in overlay (for debugging/feedback)
        this.triggerOverlayFlash();
    }
    
    // Trigger visual flash effect in detection overlay
    triggerOverlayFlash() {
        const overlay = document.getElementById('detection-overlay');
        if (overlay) {
            overlay.style.backgroundColor = 'rgba(239, 68, 68, 0.9)';
            setTimeout(() => {
                overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            }, 200);
        }
    }
    
    // Show visual notification
    showNotification(alertRegions) {
        const notification = document.createElement('div');
        notification.className = 'touch-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">⚠️</div>
                <div class="notification-text">
                    <strong>Touch Detected!</strong>
                    <br>Region: ${alertRegions.join(', ')}
                </div>
            </div>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(239, 68, 68, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            max-width: 300px;
            font-size: 14px;
        `;
        
        // Add animation keyframes if not already present
        if (!document.querySelector('#notification-animations')) {
            const style = document.createElement('style');
            style.id = 'notification-animations';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .notification-icon {
                    font-size: 24px;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    // Show positive reinforcement notification
    showPositiveNotification() {
        const notification = document.createElement('div');
        notification.className = 'touch-notification positive';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">✅</div>
                <div class="notification-text">
                    <strong>Mindful Moment!</strong>
                    <br>Great awareness stopping yourself
                </div>
            </div>
        `;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
            max-width: 300px;
            font-size: 14px;
        `;
        
        document.body.appendChild(notification);
        
        // Remove notification after 2.5 seconds (shorter than alert notifications)
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 2500);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MindfulTouchApp();
});

// Export for potential external use
window.MindfulTouchApp = MindfulTouchApp;
