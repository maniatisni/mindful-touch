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
                    this.showError('Connection timeout. Could not connect to detection service.');
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
                    this.showError('Could not connect to detection service. Make sure the backend is running.');
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
                
                // Backend should be running and WebSocket server available now
                this.connectWebSocket();
                
                // Verify connection with health check
                setTimeout(async () => {
                    try {
                        await invoke('check_backend_health');
                    } catch (e) {
                        // Health check failed - continue anyway
                    }
                }, 2000);
                
                this.isDetectionRunning = true;
                this.sessionStartTime = Date.now();
                button.textContent = 'Stop Detection';
                button.disabled = false;
                
                // Update camera placeholder
                this.updateCameraDisplay();
                
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
        placeholder.innerHTML = `
            <div class="camera-active">
                <div class="camera-icon">🔴</div>
                <p>Detection Active</p>
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
                <button id="start-detection" class="primary-button">Stop Detection</button>
            </div>
        `;
        
        // Re-attach event listener to new button
        const newButton = document.getElementById('start-detection');
        newButton.addEventListener('click', () => this.toggleDetection());
    }

    resetCameraDisplay() {
        const placeholder = document.getElementById('camera-placeholder');
        placeholder.innerHTML = `
            <div class="camera-icon">📹</div>
            <p>Camera feed will appear here</p>
            <button id="start-detection" class="primary-button">Start Detection</button>
        `;
        
        // Re-attach event listener
        const button = document.getElementById('start-detection');
        button.addEventListener('click', () => this.toggleDetection());
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
                handsStatus.textContent = data.hands_detected ? 'Detected ✓' : 'Not detected ✗';
                handsStatus.style.color = data.hands_detected ? '#10b981' : '#ef4444';
            }
            
            if (faceStatus) {
                faceStatus.textContent = data.face_detected ? 'Detected ✓' : 'Not detected ✗';
                faceStatus.style.color = data.face_detected ? '#10b981' : '#ef4444';
            }
        }
        
        this.updateUI();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MindfulTouchApp();
});

// Export for potential external use
window.MindfulTouchApp = MindfulTouchApp;