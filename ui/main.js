// Mindful Touch - Frontend JavaScript
// Check if Tauri is available
let invoke;
if (window.__TAURI__ && window.__TAURI__.tauri) {
    invoke = window.__TAURI__.tauri.invoke;
    console.log('Tauri API found');
} else {
    console.error('Tauri API not found');
    // Fallback function for testing
    invoke = async (cmd, args) => {
        console.log(`Mock invoke: ${cmd}`, args);
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
        
        this.init();
    }

    async init() {
        console.log('Initializing Mindful Touch App...');
        console.log('Window.__TAURI__ available:', !!window.__TAURI__);
        console.log('Window.__TAURI__.tauri available:', !!(window.__TAURI__ && window.__TAURI__.tauri));
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize UI
        this.updateUI();
        
        // Wait a bit for Tauri to initialize
        setTimeout(async () => {
            await this.testTauriConnection();
        }, 500);
    }

    async testTauriConnection() {
        try {
            console.log('Testing Tauri connection...');
            const response = await invoke('greet', { name: 'Mindful Touch' });
            console.log('Tauri connection successful:', response);
            this.updateConnectionStatus(true);
        } catch (error) {
            console.error('Failed to connect to Tauri:', error);
            console.error('Error details:', error);
            console.error('Error type:', typeof error);
            this.updateConnectionStatus(false);
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
        console.log('Toggle detection called');
        const button = document.getElementById('start-detection');
        
        if (!this.isDetectionRunning) {
            try {
                console.log('Starting detection...');
                button.textContent = 'Starting...';
                button.disabled = true;
                
                // Start Python backend
                console.log('Calling start_python_backend...');
                const result = await invoke('start_python_backend');
                console.log('Python backend result:', result);
                
                this.isDetectionRunning = true;
                this.sessionStartTime = Date.now();
                button.textContent = 'Stop Detection';
                button.disabled = false;
                
                // Update camera placeholder
                this.updateCameraDisplay();
                
                console.log('Detection started successfully');
            } catch (error) {
                console.error('Failed to start detection:', error);
                console.error('Error details:', error);
                button.textContent = 'Start Detection';
                button.disabled = false;
                this.showError(`Failed to start detection: ${error.message || error}`);
            }
        } else {
            console.log('Stopping detection...');
            this.isDetectionRunning = false;
            this.sessionStartTime = null;
            button.textContent = 'Start Detection';
            
            // Reset camera display
            this.resetCameraDisplay();
            
            console.log('Detection stopped');
        }
    }

    async toggleRegion(region, enabled) {
        try {
            const response = await invoke('toggle_region', { region: region });
            console.log('Region toggle result:', response);
            
            // Update UI to reflect change
            const label = document.querySelector(`#${region}-toggle + .region-label`);
            if (label) {
                label.style.fontWeight = enabled ? '600' : '500';
                label.style.color = enabled ? '#667eea' : '#4a5568';
            }
        } catch (error) {
            console.error('Failed to toggle region:', error);
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

    // Method to receive detection data from Python backend
    onDetectionData(data) {
        // This will be called when we receive detection data
        this.statistics.totalDetections++;
        
        if (data.alerts_active && data.alerts_active.length > 0) {
            this.statistics.mostActiveRegion = data.alerts_active[0];
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