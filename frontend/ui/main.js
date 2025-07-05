// Mindful Touch - Frontend JavaScript
// Check if Tauri is available (Tauri v2 format)
let invoke;
let isPermissionGranted, requestPermission, sendNotification;

if (window.__TAURI__ && window.__TAURI__.core) {
    invoke = window.__TAURI__.core.invoke;
} else if (window.__TAURI__ && window.__TAURI__.tauri) {
    invoke = window.__TAURI__.tauri.invoke;
} else {
    // Fallback function for testing
    invoke = async (cmd, args) => {
        console.log(`Mock invoke: ${cmd}`, args);
        return `Mock response for ${cmd}`;
    };
}

// Try to access notification functions from plugin
if (window.__TAURI_PLUGIN_NOTIFICATION__) {
    const plugin = window.__TAURI_PLUGIN_NOTIFICATION__;
    isPermissionGranted = plugin.isPermissionGranted;
    requestPermission = plugin.requestPermission;
    sendNotification = plugin.sendNotification;
    console.log('Notification plugin loaded from __TAURI_PLUGIN_NOTIFICATION__');
} else if (window.__TAURI__ && window.__TAURI__.notification) {
    const plugin = window.__TAURI__.notification;
    isPermissionGranted = plugin.isPermissionGranted;
    requestPermission = plugin.requestPermission;
    sendNotification = plugin.sendNotification;
    console.log('Notification plugin loaded from __TAURI__.notification');
} else {
    // Fallback functions
    console.warn('Notification plugin not found, using fallback');
    isPermissionGranted = async () => {
        console.log('Mock: notification permission check');
        return true;
    };
    requestPermission = async () => {
        console.log('Mock: notification permission request');
        return 'granted';
    };
    sendNotification = async (options) => {
        console.log('Mock notification:', options);
        alert(`Notification: ${options.title}\n${options.body}`);
    };
}

console.log('Tauri setup complete:', { invoke: !!invoke, isPermissionGranted: !!isPermissionGranted, sendNotification: !!sendNotification });

class MindfulTouchApp {
    constructor() {
        this.isDetectionRunning = false;
        this.sessionStartTime = null;
        this.statistics = {
            totalDetections: 0, // Only count actual alerts (after delay)
            sessionDuration: 0,
            mindfulStops: 0 // Count when user stops touching before alert
        };
        
        // Notification settings - system notifications enabled by default
        this.notificationSettings = {
            enabled: true,
            soundEnabled: true,
            delaySeconds: 3,
            selectedSound: 'default' // Use system default sound
        };
        
        // Notification permission state
        this.notificationPermission = null;
        
        // Alert delay management
        this.alertDelayTimeouts = new Map(); // Track active delays by region
        this.activeAlerts = new Set(); // Track which regions are currently alerting
        
        // Audio context for playing sounds (fallback only)
        this.audioContext = null;
        this.soundBuffers = {};
        
        // WebSocket connection
        this.websocket = null;
        this.wsUrl = 'ws://localhost:8765';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Heartbeat
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null;
        this.heartbeatFailures = 0;
        
        // Frame throttling disabled for real-time
        this.lastFrameUpdate = 0;
        this.frameThrottleMs = 0; // No throttling for real-time display
        
        this.init();
    }

    async init() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize UI
        this.updateUI();
        
        // Wait a bit for Tauri to initialize
        setTimeout(async () => {
            await this.testTauriConnection();
            await this.initializeNotifications();
        }, 500);
    }

    connectWebSocket() {
        // Close any existing connection
        if (this.websocket) {
            try {
                if (this.websocket.readyState === WebSocket.OPEN || 
                    this.websocket.readyState === WebSocket.CONNECTING) {
                    this.websocket.close();
                }
            } catch (e) {
                // Ignore close errors
            }
            this.websocket = null;
        }
        
        try {
            this.websocket = new WebSocket(this.wsUrl);
            
            // Set a timeout for initial connection
            const connectionTimeout = setTimeout(() => {
                if (this.websocket && this.websocket.readyState !== WebSocket.OPEN) {
                    this.websocket.close();
                    this.showError('Connection timeout. Please try again.');
                }
            }, 5000);
            
            this.websocket.onopen = () => {
                clearTimeout(connectionTimeout);
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                
                // Start heartbeat
                this.startHeartbeat();
                
                // Send ping to test connection
                this.sendWebSocketMessage({ type: 'ping' });
                
                // Update button text if still showing connecting
                const button = document.getElementById('start-detection');
                if (button && button.textContent === 'Connecting...') {
                    button.textContent = 'Stop Detection';
                    button.disabled = false;
                }
            };
            
            this.websocket.onmessage = (event) => {
                // Reset failure counter on any message
                this.heartbeatFailures = 0;
                this.handleWebSocketMessage(event.data);
            };
            
            this.websocket.onclose = (event) => {
                clearTimeout(connectionTimeout);
                this.updateConnectionStatus(false);
                
                // Only attempt reconnect if detection is running
                if (this.isDetectionRunning) {
                    this.attemptReconnect();
                }
                
                // Stop heartbeat
                this.stopHeartbeat();
            };
            
            this.websocket.onerror = (error) => {
                clearTimeout(connectionTimeout);
                this.updateConnectionStatus(false);
                
                // Show user-friendly error if initial connection fails
                if (this.reconnectAttempts === 0) {
                    this.showError('Could not connect to detection service.');
                    
                    // Reset UI state on connection error
                    const button = document.getElementById('start-detection');
                    if (button && this.isDetectionRunning) {
                        button.textContent = 'Start Detection';
                        button.disabled = false;
                        this.isDetectionRunning = false;
                        this.sessionStartTime = null;
                        this.resetCameraDisplay();
                    }
                }
            };
            
        } catch (error) {
            this.updateConnectionStatus(false);
            this.showError('Failed to create WebSocket connection');
        }
    }
    
    // Heartbeat to keep connection alive
    startHeartbeat() {
        this.stopHeartbeat(); // Clear any existing interval
        this.heartbeatFailures = 0;
        
        // Send ping every 10 seconds
        this.heartbeatInterval = setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.sendWebSocketMessage({ type: 'ping' });
                
                // Check for response within 5 seconds
                this.heartbeatTimeout = setTimeout(() => {
                    this.heartbeatFailures++;
                    
                    // If we miss 3 heartbeats, reconnect
                    if (this.heartbeatFailures >= 3) {
                        if (this.websocket) {
                            this.websocket.close();
                        }
                    }
                }, 5000);
            }
        }, 10000);
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
        
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
    }

    sendWebSocketMessage(message) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify(message));
        }
    }

    handleWebSocketMessage(data) {
        // Reset heartbeat failure counter on any message from server
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
        this.heartbeatFailures = 0;
        
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'detection_data':
                    this.onDetectionData(message.data);
                    // Handle camera frame if present
                    if (message.data.frame) {
                        this.displayCameraFrame(message.data.frame);
                    }
                    break;
                    
                case 'region_toggle_response':
                    break;
                    
                case 'pong':
                    break;
                    
                default:
                    break;
            }
        } catch (error) {
            // Ignore message parsing errors
        }
    }

    async waitForBackendReady() {
        const maxAttempts = 30; // 30 seconds max wait
        let attempts = 0;
        
        const checkBackend = async () => {
            attempts++;
            
            try {
                // Try to connect to WebSocket to test if backend is ready
                const testSocket = new WebSocket(this.wsUrl);
                
                return new Promise((resolve, reject) => {
                    const timeout = setTimeout(() => {
                        testSocket.close();
                        reject(new Error('Connection timeout'));
                    }, 2000);
                    
                    testSocket.onopen = () => {
                        clearTimeout(timeout);
                        testSocket.close();
                        resolve(true);
                    };
                    
                    testSocket.onerror = () => {
                        clearTimeout(timeout);
                        reject(new Error('Connection failed'));
                    };
                });
            } catch (error) {
                throw error;
            }
        };
        
        // Update button text to show progress
        const button = document.getElementById('start-detection');
        
        while (attempts < maxAttempts) {
            try {
                button.textContent = 'Starting...';
                await checkBackend();
                
                // Backend is ready, connect WebSocket
                button.textContent = 'Connecting...';
                this.connectWebSocket();
                
                // Set detection as running only after backend is confirmed ready
                this.isDetectionRunning = true;
                this.sessionStartTime = Date.now();
                button.textContent = 'Stop Detection';
                button.disabled = false;
                
                // Update camera display only after backend is ready
                this.updateCameraDisplay();
                return;
                
            } catch (error) {
                // Wait 1 second before next attempt
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        
        // Failed to connect after max attempts
        button.textContent = 'Start Detection';
        button.disabled = false;
        this.isDetectionRunning = false;
        this.showError('Backend failed to start. Please try again.');
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            
            setTimeout(() => {
                this.connectWebSocket();
            }, 2000 * this.reconnectAttempts); // Exponential backoff
        } else {
            this.showError('Lost connection to detection service');
        }
    }

    async testTauriConnection() {
        try {
            await invoke('greet', { name: 'Mindful Touch' });
        } catch (error) {
            // Tauri connection test failed - ignore for now
        }
    }
    
    async initializeNotifications() {
        try {
            console.log('Initializing notifications...');
            // Check if notification permission is granted
            this.notificationPermission = await isPermissionGranted();
            console.log('Notification permission status:', this.notificationPermission);
            
            // If not granted, we'll request permission when first needed
            if (!this.notificationPermission) {
                console.log('Notification permission not granted, will request on first use');
            } else {
                console.log('Notification permission already granted');
            }
        } catch (error) {
            console.warn('Failed to check notification permission:', error);
            this.notificationPermission = false;
        }
    }
    
    async ensureNotificationPermission() {
        console.log('Current permission state:', this.notificationPermission);
        
        if (this.notificationPermission === null || this.notificationPermission === false) {
            try {
                console.log('Requesting notification permission...');
                const permission = await requestPermission();
                console.log('Permission response:', permission);
                this.notificationPermission = permission === 'granted';
                
                if (!this.notificationPermission) {
                    console.warn('Permission denied:', permission);
                    this.showError(`Notification permission ${permission}. Please enable in System Settings > Notifications.`);
                } else {
                    console.log('Permission granted successfully');
                }
            } catch (error) {
                console.error('Failed to request notification permission:', error);
                this.notificationPermission = false;
            }
        }
        console.log('Final permission state:', this.notificationPermission);
        return this.notificationPermission;
    }

    setupEventListeners() {
        // Start Detection Button
        const startButton = document.getElementById('start-detection');
        startButton.addEventListener('click', () => this.toggleDetection());

        // Region Toggle Switches
        const regions = ['scalp', 'eyebrows', 'eyes', 'mouth', 'beard'];
        regions.forEach(region => {
            const toggle = document.getElementById(`${region}-toggle`);
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
                button.textContent = 'Starting...';
                button.disabled = true;
                
                // Start Python backend
                await invoke('start_python_backend');
                
                // Wait for backend to be ready with health check polling
                // Don't set detection running until backend is confirmed ready
                await this.waitForBackendReady();
                
            } catch (error) {
                button.textContent = 'Start Detection';
                button.disabled = false;
                this.showError(`Failed to start detection: ${error.message || error}`);
            }
        } else {
            this.isDetectionRunning = false;
            this.sessionStartTime = null;
            button.textContent = 'Start Detection';
            
            // Stop heartbeat
            this.stopHeartbeat();
            
            // Close WebSocket connection
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }
            
            // Stop Python backend
            try {
                await invoke('stop_python_backend');
            } catch (error) {
                // Ignore stop errors
            }
            
            // Reset camera display
            this.resetCameraDisplay();
        }
    }

    async toggleRegion(region, enabled) {
        try {
            // Send via WebSocket if connected
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.sendWebSocketMessage({
                    type: 'toggle_region',
                    region: region,
                    enabled: enabled
                });
            }
            
            // Update UI to reflect change immediately
            const label = document.querySelector(`#${region}-toggle`).parentElement.querySelector('.region-label');
            if (label) {
                label.style.fontWeight = enabled ? '600' : '500';
                label.style.color = enabled ? '#667eea' : '#4a5568';
            }
            
        } catch (error) {
            // Ignore toggle errors
        }
    }

    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connection-status');
        if (isConnected) {
            statusElement.textContent = 'Active';
            statusElement.className = 'status-indicator online';
        } else {
            statusElement.textContent = 'Ready';
            statusElement.className = 'status-indicator offline';
        }
    }

    updateCameraDisplay() {
        const placeholder = document.getElementById('camera-placeholder');
        const cameraFeed = document.getElementById('camera-feed');
        
        // Hide placeholder and show camera feed
        placeholder.style.display = 'none';
        cameraFeed.style.display = 'block';
        
        // Add detection status overlay with fixed dimensions
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
            </div>
        `;
        
        // Create stop button with fixed width to prevent size changes
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
            width: 110px;
            text-align: center;
        `;
        
        // Add event listener before appending
        stopButton.addEventListener('click', () => {
            console.log('Stop button clicked');
            this.toggleDetection();
        });
        
        overlay.appendChild(stopButton);
        
        const cameraContainer = document.querySelector('.camera-container');
        cameraContainer.style.position = 'relative';
        cameraContainer.appendChild(overlay);
    }

    resetCameraDisplay() {
        const placeholder = document.getElementById('camera-placeholder');
        const cameraFeed = document.getElementById('camera-feed');
        const overlay = document.getElementById('detection-overlay');
        
        // Show placeholder and hide camera feed
        placeholder.style.display = 'block';
        cameraFeed.style.display = 'none';
        
        // Remove overlay if it exists
        if (overlay) {
            overlay.remove();
        }
        
        placeholder.innerHTML = `
            <div class="camera-icon">📹</div>
            <p>Camera feed will appear here</p>
            <button id="start-detection" class="primary-button" style="width: 140px; text-align: center;">Start Detection</button>
        `;
        
        // Re-attach event listener
        const button = document.getElementById('start-detection');
        button.addEventListener('click', () => this.toggleDetection());
    }

    displayCameraFrame(frameBase64) {
        const cameraFeed = document.getElementById('camera-feed');
        if (cameraFeed && this.isDetectionRunning) {
            // Use more efficient image loading with object URL
            try {
                // Convert base64 to blob for better performance
                const byteCharacters = atob(frameBase64);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                
                // Auto-detect image type (PNG or JPEG) based on header
                const isPNG = byteArray[0] === 0x89 && byteArray[1] === 0x50 && byteArray[2] === 0x4E && byteArray[3] === 0x47;
                const mimeType = isPNG ? 'image/png' : 'image/jpeg';
                const blob = new Blob([byteArray], { type: mimeType });
                
                // Revoke previous object URL to prevent memory leaks
                if (cameraFeed.src && cameraFeed.src.startsWith('blob:')) {
                    URL.revokeObjectURL(cameraFeed.src);
                }
                
                // Set new object URL
                cameraFeed.src = URL.createObjectURL(blob);
            } catch (error) {
                console.warn('Failed to update camera frame:', error);
                // Fallback to base64
                cameraFeed.src = `data:image/jpeg;base64,${frameBase64}`;
            }
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
        
        const contactCount = data.contact_points || 0;
        const alertsActive = data.alerts_active || [];
        
        contactInfo.innerHTML = `
            <div style="color: ${contactCount > 0 ? '#ef4444' : '#10b981'};">
                Contacts: ${contactCount}
            </div>
            ${alertsActive.length > 0 ? 
                `<div style="color: #ef4444; font-weight: bold;">
                    ⚠️ Alert: ${alertsActive.join(', ')}
                </div>` : 
                '<div style="color: #10b981;">No alerts</div>'
            }
        `;
        
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
        
        // No system notifications toggle - always use system notifications
        
        // Delay slider
        const delaySlider = document.getElementById('notification-delay');
        const delayValue = document.getElementById('delay-value');
        delaySlider.addEventListener('input', (e) => {
            this.notificationSettings.delaySeconds = parseInt(e.target.value);
            delayValue.textContent = `${e.target.value}s`;
        });
        
        // Sound selection buttons
        const soundSelectButtons = document.querySelectorAll('.sound-select-button');
        soundSelectButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Remove active class from all buttons
                soundSelectButtons.forEach(btn => btn.classList.remove('active'));
                // Add active class to clicked button
                e.target.classList.add('active');
                // Update selected sound - map to platform-specific system sounds
                const soundType = e.target.dataset.sound;
                this.notificationSettings.selectedSound = this.mapSoundToPlatform(soundType);
                console.log('Selected sound:', this.notificationSettings.selectedSound);
            });
        });
        
        // Test sound button - always test system notification
        const testButton = document.getElementById('test-sound-btn');
        testButton.addEventListener('click', async () => {
            await this.sendTestSystemNotification();
        });
        
        // Audio context disabled - using system notifications by default
        // this.initializeAudio();
        
        // Set initial sound based on platform
        this.notificationSettings.selectedSound = this.mapSoundToPlatform('chime');
        
        // Update test button text for system notifications
        if (testButton) {
            testButton.textContent = '🔔 Test System Notification';
        }
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
    
    // Send test system notification
    async sendTestSystemNotification() {
        try {
            console.log('Testing system notification...');
            // Ensure we have permission
            if (!await this.ensureNotificationPermission()) {
                this.showError('Notification permission required for system notifications');
                return;
            }
            
            const platform = this.detectPlatform();
            const platformName = platform === 'macos' ? 'macOS' : platform === 'windows' ? 'Windows' : 'Linux';
            
            console.log('Platform detected:', platform, 'Sound:', this.notificationSettings.selectedSound);
            
            // Test different sound formats sequentially
            const soundTests = [
                { name: 'Current Setting', sound: this.notificationSettings.selectedSound },
                { name: 'Default', sound: 'default' },
                { name: 'Null', sound: null },
                { name: 'Sosumi', sound: 'Sosumi' },
                { name: 'Basso', sound: 'Basso' },
                { name: 'Tink', sound: 'Tink' },
                { name: 'No Sound Property', sound: undefined }
            ];
            
            for (let i = 0; i < soundTests.length; i++) {
                const test = soundTests[i];
                console.log(`Testing sound ${i + 1}/${soundTests.length}: ${test.name} (${test.sound})`);
                
                const notificationOptions = {
                    title: `Test ${i + 1}/${soundTests.length}: ${test.name}`,
                    body: `Sound: ${test.sound || 'undefined'}`,
                };
                
                // Only add sound property if it's not undefined
                if (test.sound !== undefined) {
                    notificationOptions.sound = test.sound;
                }
                
                await sendNotification(notificationOptions);
                
                // Wait 2 seconds between tests
                if (i < soundTests.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                }
            }
            
            console.log('All test notifications sent successfully');
            
        } catch (error) {
            console.error('Test notification failed:', error);
            this.showError(`Failed to send test notification: ${error.message}`);
        }
    }
    
    // Handle alert delays - start timers for new regions, maintain existing ones
    handleAlertDelays(alertRegions) {
        const delayMs = this.notificationSettings.delaySeconds * 1000;
        
        alertRegions.forEach(region => {
            // If this region is not already in delay or alerting, start delay timer
            if (!this.alertDelayTimeouts.has(region) && !this.activeAlerts.has(region)) {
                
                if (delayMs === 0) {
                    // No delay - trigger immediately
                    this.triggerAlert([region]);
                } else {
                    // Start delay timer
                    const timeoutId = setTimeout(() => {
                        this.alertDelayTimeouts.delete(region);
                        this.triggerAlert([region]);
                    }, delayMs);
                    
                    this.alertDelayTimeouts.set(region, timeoutId);
                }
            }
        });
        
        // Cancel delays for regions that are no longer active
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
    async triggerAlert(alertRegions) {
        // Add to active alerts
        alertRegions.forEach(region => this.activeAlerts.add(region));
        
        // Count as actual detection (only when alert actually fires)
        this.statistics.totalDetections++;
        
        // Always use system notifications if enabled
        if (this.notificationSettings.enabled) {
            await this.sendSystemNotification(alertRegions);
        }
        
        // Trigger visual flash in overlay
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
    async showPositiveNotification() {
        // Always use system notifications
        if (await this.ensureNotificationPermission()) {
            try {
                await sendNotification({
                    title: 'Mindful Moment! ✅',
                    body: 'Great awareness stopping yourself',
                    sound: null // No sound for positive reinforcement
                });
                return;
            } catch (error) {
                console.warn('System notification failed, falling back to visual:', error);
            }
        }
        
        // Fallback to visual notification
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
    
    // Map sound types to platform-specific system sounds
    mapSoundToPlatform(soundType) {
        // Detect platform (simplified detection)
        const platform = this.detectPlatform();
        
        const soundMaps = {
            'macos': {
                'chime': 'Glass',  // Known to exist in /System/Library/Sounds/
                'beep': 'Ping',    // Known to exist in /System/Library/Sounds/
                'gentle': 'Purr'   // Known to exist in /System/Library/Sounds/
            },
            'windows': {
                'chime': 'Notification.Default',
                'beep': 'Notification.Reminder', 
                'gentle': 'Notification.SMS'
            },
            'linux': {
                'chime': 'message-new-instant',
                'beep': 'complete',
                'gentle': 'bell'
            }
        };
        
        const selectedSound = soundMaps[platform]?.[soundType] || 'default';
        console.log(`Platform: ${platform}, Type: ${soundType}, Selected: ${selectedSound}`);
        return selectedSound;
    }
    
    // Simple platform detection
    detectPlatform() {
        // Try to detect via Tauri API first
        if (window.__TAURI__?.os) {
            return window.__TAURI__.os.platform();
        }
        
        // Fallback to user agent detection
        const userAgent = navigator.userAgent.toLowerCase();
        if (userAgent.includes('mac')) return 'macos';
        if (userAgent.includes('win')) return 'windows';
        if (userAgent.includes('linux')) return 'linux';
        
        return 'unknown';
    }
    
    // Send system notification for alerts
    async sendSystemNotification(alertRegions) {
        try {
            // Ensure we have permission
            if (!await this.ensureNotificationPermission()) {
                console.warn('No notification permission, falling back to visual notification');
                this.showNotification(alertRegions);
                return;
            }
            
            // Send system notification with platform-appropriate sound
            await sendNotification({
                title: 'Touch Detected! ⚠️',
                body: `Region: ${alertRegions.join(', ')}`,
                sound: this.notificationSettings.soundEnabled ? this.notificationSettings.selectedSound : null
            });
            
        } catch (error) {
            console.warn('System notification failed:', error);
            // Fallback to visual notification
            this.showNotification(alertRegions);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MindfulTouchApp();
});

// Export for potential external use
window.MindfulTouchApp = MindfulTouchApp;
