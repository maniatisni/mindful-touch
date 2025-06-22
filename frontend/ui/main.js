// Mindful Touch - Frontend JavaScript
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
            totalDetections: 0,
            sessionDuration: 0,
            mostActiveRegion: 'None'
        };
        
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
        document.getElementById('most-active-region').textContent = this.statistics.mostActiveRegion;
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
        // Update detection statistics
        if (data.alerts_active && data.alerts_active.length > 0) {
            this.statistics.totalDetections++;
            this.statistics.mostActiveRegion = data.alerts_active[0];
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
        
        // Add visual flash effect for alerts
        if (alertsActive.length > 0) {
            overlay.style.backgroundColor = 'rgba(239, 68, 68, 0.9)';
            setTimeout(() => {
                overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            }, 200);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MindfulTouchApp();
});

// Export for potential external use
window.MindfulTouchApp = MindfulTouchApp;