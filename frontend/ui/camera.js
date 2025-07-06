/**
 * Camera utilities for JavaScript MediaPipe detection
 * Handles camera access and video stream management
 */

class CameraManager {
    constructor() {
        this.stream = null;
        this.video = null;
        this.isRunning = false;
        this.onFrameCallback = null;
        this.animationFrameId = null;
    }
    
    async initialize() {
        try {
            console.log('Requesting camera access...');
            
            // Request camera access
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    frameRate: { ideal: 30 },
                    facingMode: 'user' // Front-facing camera
                },
                audio: false
            });
            
            // Create video element
            this.video = document.createElement('video');
            this.video.srcObject = this.stream;
            this.video.autoplay = true;
            this.video.muted = true;
            this.video.playsInline = true;
            
            // Wait for video to be ready
            await new Promise((resolve, reject) => {
                this.video.onloadedmetadata = () => {
                    this.video.play().then(resolve).catch(reject);
                };
                this.video.onerror = reject;
            });
            
            console.log(`Camera initialized: ${this.video.videoWidth}x${this.video.videoHeight}`);
            return true;
            
        } catch (error) {
            console.error('Failed to initialize camera:', error);
            
            if (error.name === 'NotAllowedError') {
                throw new Error('Camera access denied. Please allow camera permissions and refresh.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No camera found. Please connect a camera and refresh.');
            } else {
                throw new Error(`Camera initialization failed: ${error.message}`);
            }
        }
    }
    
    startCapture(onFrameCallback) {
        if (!this.video || !this.stream) {
            throw new Error('Camera not initialized');
        }
        
        this.onFrameCallback = onFrameCallback;
        this.isRunning = true;
        
        const captureFrame = () => {
            if (!this.isRunning) return;
            
            if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
                const timestamp = performance.now();
                
                // Call the frame callback with video element and timestamp
                if (this.onFrameCallback) {
                    this.onFrameCallback(this.video, timestamp);
                }
            }
            
            // Request next frame
            this.animationFrameId = requestAnimationFrame(captureFrame);
        };
        
        // Start capturing frames
        captureFrame();
        console.log('Camera capture started');
    }
    
    stopCapture() {
        this.isRunning = false;
        
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        
        console.log('Camera capture stopped');
    }
    
    getVideoElement() {
        return this.video;
    }
    
    getVideoSize() {
        if (!this.video) return { width: 0, height: 0 };
        return {
            width: this.video.videoWidth,
            height: this.video.videoHeight
        };
    }
    
    captureFrame() {
        if (!this.video) return null;
        
        // Create canvas to capture frame
        const canvas = document.createElement('canvas');
        canvas.width = this.video.videoWidth;
        canvas.height = this.video.videoHeight;
        
        const ctx = canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0);
        
        return canvas.toDataURL('image/jpeg', 0.8);
    }
    
    destroy() {
        this.stopCapture();
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.video) {
            this.video.srcObject = null;
            this.video = null;
        }
        
        console.log('Camera destroyed');
    }
}

export { CameraManager };
