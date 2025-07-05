# Mindful Touch - Project Documentation

## Project Overview

Mindful Touch is a gentle awareness tool designed to help users develop mindful hand movement tracking. The application detects when hands touch specific facial regions (scalp, eyebrows, eyes, mouth, beard) and provides real-time feedback to promote awareness of unconscious touching habits.

## Architecture & Technologies

### Backend (Python)
- **Framework**: Custom Python application with MediaPipe
- **Computer Vision**: MediaPipe for hand and face detection
- **Real-time Communication**: WebSocket server (websockets library)
- **Dependencies**: OpenCV, MediaPipe, asyncio
- **Package Management**: UV (Python package manager)

### Frontend (Desktop App)
- **Framework**: Tauri (Rust + JavaScript/HTML/CSS)
- **UI**: Vanilla JavaScript with modern CSS
- **Communication**: WebSocket client for real-time data
- **Platform**: Cross-platform desktop application

### Key Components

1. **Multi-Region Detector** (`backend/detection/multi_region_detector.py`)
   - Face mesh detection using MediaPipe
   - Hand landmark detection
   - Configurable facial regions (scalp, eyebrows, eyes, mouth, beard)
   - Contact point calculation and proximity detection

2. **WebSocket Server** (`backend/server/websocket_server.py`)
   - Real-time communication between backend and frontend
   - Handles region toggle requests
   - Broadcasts detection data to connected clients
   - Thread-safe operation with asyncio

3. **Tauri Frontend** (`frontend/`)
   - Desktop application wrapper
   - Process management for Python backend
   - WebSocket client for real-time updates
   - Region toggle controls and statistics display

## How to Use the Codebase

### Prerequisites
- Python 3.8+
- UV package manager (`pip install uv`)
- Rust and Cargo (for Tauri)
- Node.js (for Tauri frontend dependencies)

### Development Setup

1. **Install Dependencies**
   ```bash
   # Install Python dependencies
   uv sync
   
   # Install Tauri CLI
   cargo install tauri-cli
   ```

2. **Run Backend Standalone**
   ```bash
   # GUI mode
   uv run python -m backend.detection.main
   
   # Headless mode (for frontend integration)
   uv run python -m backend.detection.main --headless
   
   # Mock camera mode (for CI/testing)
   uv run python -m backend.detection.main --headless --mock-camera
   ```

3. **Run Frontend**
   ```bash
   cd frontend/src-tauri
   cargo tauri dev
   ```

4. **Run Tests**
   ```bash
   # Python tests
   uv run pytest
   
   # Integration tests
   uv run python scripts/run_integration_tests.py
   
   # Mock camera tests
   uv run python scripts/test_mock_camera.py
   ```

### Build for Production
```bash
cd frontend/src-tauri
cargo tauri build
```

## Quick Testing

### Test WebSocket Connection
```bash
# Start backend
uv run python -m backend.detection.main --headless --mock-camera

# Test connection
uv run python3 -c "import asyncio, websockets, json; asyncio.run((lambda: websockets.connect('ws://localhost:8765').send(json.dumps({'type': 'ping'}))()))"
```

### Test Frontend
```bash
cd frontend/src-tauri && cargo check
cargo tauri dev
```

## Current Implementation Status

### ✅ Implemented Features

1. **Core Detection Engine**
   - Multi-region face detection (5 configurable regions)
   - Hand landmark detection with MediaPipe
   - Contact point calculation and proximity alerts
   - Real-time frame processing

2. **WebSocket Integration**
   - Bidirectional communication between backend and frontend
   - Real-time detection data streaming
   - Region toggle functionality via WebSocket messages
   - Ping/pong heartbeat mechanism

3. **Desktop Application**
   - Tauri-based cross-platform desktop app
   - Modern UI with region toggle controls
   - Session statistics and timer
   - Connection status indicators

4. **Testing Infrastructure**
   - Comprehensive pytest test suite (14 tests passing)
   - WebSocket integration tests
   - Mock camera for CI/CD environments
   - Debug tools for troubleshooting

5. **Development Tools**
   - Mock camera implementation for testing
   - Debug scripts for frontend-backend integration
   - Automated formatting with ruff
   - Git integration with proper commit workflows

6. **Tauri Integration** ✅ **COMPLETED (January 2025)**
   - Fixed Tauri API loading issue (v2 compatibility)
   - Automatic Python backend process management
   - Proper connection status feedback
   - Process lifecycle handling (start/stop backend)
   - WebSocket connection works seamlessly with Tauri

### ✅ Core System Status

- **WebSocket Communication**: ✅ Working correctly between backend and frontend
- **Backend Process Management**: ✅ Fully automated via Tauri - no manual backend startup needed
- **Process Lifecycle**: ✅ Properly handled - backend starts/stops with detection
- **Tauri-Frontend Integration**: ✅ Complete - API calls working, connection status accurate
- **Codebase**: ✅ Cleaned up, reduced bloat significantly

## Next Steps & Roadmap

### 🎉 CURRENT SESSION STATUS (December 29, 2024) - **PRODUCTION BUILDS COMPLETED**

**BRANCH**: `fix/production-builds` ✅ **READY FOR MERGE**
**TAG**: `v1.0.1-test` ✅ **SUCCESSFUL BUILD WITH ARTIFACTS**

**✅ PRODUCTION BUILD SUCCESS ACHIEVED**

**Problem SOLVED**: macOS production builds now work correctly with camera permissions and proper backend bundling!

**✅ Final Resolution**:
1. ✅ **GitHub Actions** builds PyInstaller executable successfully
2. ✅ **Backend Bundling** copies to correct `bin/mindful-touch-backend-{target}` location
3. ✅ **Tauri Integration** finds and launches backend executable correctly
4. ✅ **Camera Permissions** automatically added to Info.plist via GitHub Actions
5. ✅ **Cross-Mac Testing** confirmed working on multiple machines

**✅ Current State**: 
- PyInstaller spec file: `backend_standalone.spec` ✅ Working correctly
- GitHub Actions workflow: ✅ Successfully builds and uploads artifacts (.app + .dmg)
- Tauri config: ✅ Simplified external binary configuration
- Camera permissions: ✅ Automatically injected into macOS Info.plist
- Backend detection: ✅ Enhanced logging and fallback to MockCamera

**✅ COMPLETED FEATURES**:
- ✅ **macOS Production Builds**: Fully working .app and .dmg distribution
- ✅ **Camera Permissions**: Proper NSCameraUsageDescription integration
- ✅ **Backend Process Management**: Automatic startup/shutdown via Tauri
- ✅ **Enhanced Camera Detection**: Better error handling and debugging
- ✅ **Cross-Platform Compatibility**: Tested on multiple macOS machines
- ✅ **GitHub Actions CI/CD**: Automated builds with artifact uploads

**🔄 NEXT SESSION PRIORITIES**:
1. **Backend Startup Optimization**: Reduce cold start time (currently slow)
2. **Windows Build Pipeline**: Add Windows support to GitHub Actions
3. **Performance Optimization**: Frame rate and resource usage improvements

### 🔧 UPCOMING WINDOWS BUILD SUPPORT

**PRIORITY 1: Windows Build Pipeline** 📋 **PLANNED FOR NEXT SESSION**
```bash
# Enable Windows in GitHub Actions (.github/workflows/tag-release.yml)
# Uncomment the Windows matrix entry:
- platform: windows-latest
  os: windows
  args: '--target x86_64-pc-windows-msvc'
  rust-target: x86_64-pc-windows-msvc
  upload-files: |
    frontend/src-tauri/target/x86_64-pc-windows-msvc/release/bundle/msi/*.msi
    frontend/src-tauri/target/x86_64-pc-windows-msvc/release/bundle/nsis/*.exe
```

**Windows Implementation Checklist**:
- ✅ **Backend**: PyInstaller spec already configured for Windows (.exe)
- 📋 **Camera Permissions**: Research Windows camera permission requirements
- 📋 **Installer Packages**: MSI and NSIS for easy distribution
- 📋 **Icon Format**: Fix RC2175 icon format error (requires Windows .ico format)
- 📋 **Testing**: Validate on Windows 10/11 machines
- 📋 **Code Signing**: Windows Authenticode signing for distribution

**Linux Support**: Not planned - Linux users can build locally with existing tools

### 🎯 Immediate Next Tasks (After Build Issues Resolved)

**PRIORITY 1: 🚨 CRITICAL BUG - Camera Resource Leak** ⚠️ **ACTIVE ISSUE**
- **Issue**: When the Tauri app is closed, the camera light remains on indicating the backend process didn't properly release camera resources
- **Root Cause Analysis**: 
  - Backend Python process (`backend/detection/main.py`) runs in headless mode with infinite loop (`while True:`)
  - Only responds to KeyboardInterrupt, not SIGTERM/SIGINT signals from Tauri process termination
  - Camera resource cleanup (`cap.release()`) only happens in `finally` block on KeyboardInterrupt
  - Tauri process management (`frontend/src-tauri/src/main.rs`) sends SIGTERM/SIGKILL but backend doesn't listen for these signals
- **Investigation Status**: 
  - ✅ Identified the issue in backend signal handling
  - ✅ Located camera cleanup code in `run_headless_mode()` function
  - ⚠️ **ATTEMPTED FIX FAILED**: Added signal handlers and graceful shutdown but reverted for separate commit
- **Required Fix**: 
  - Add proper signal handling (SIGTERM/SIGINT) to backend Python process
  - Implement graceful camera resource cleanup on process termination
  - Improve Tauri process termination with timeout for graceful shutdown
  - Test camera light turns off immediately when app closes
- **Files to Modify**:
  - `backend/detection/main.py` - Add signal handlers and graceful shutdown
  - `frontend/src-tauri/src/main.rs` - Improve process termination timing

**PRIORITY 2: 🐌 PERFORMANCE - Slow Backend Startup** ⚠️ **OPTIMIZATION NEEDED**
- **Issue**: Backend startup is very slow, taking several seconds before detection is ready
- **Current Behavior**: 
  - Frontend shows "Starting..." then "Connecting..." for extended time
  - User waits 3-5+ seconds before detection begins
  - No visibility into what's causing the delay
- **Investigation Needed**: 
  - ⚠️ **ROOT CAUSE UNKNOWN**: Need to profile and time each startup component
  - Add timing measurements to identify bottlenecks in startup sequence
  - Profile MediaPipe initialization, camera setup, WebSocket server startup
- **Startup Sequence to Profile**:
  1. Python process launch (`invoke('start_python_backend')`)
  2. MediaPipe model loading (`MultiRegionDetector()`)
  3. Camera initialization (`initialize_camera()`)
  4. WebSocket server startup (`DetectionWebSocketServer`)
  5. First frame processing and detection ready
- **Optimization Strategy**:
  - Time each component separately to identify the bottleneck
  - Consider lazy loading of MediaPipe models
  - Optimize camera initialization with faster detection
  - Pre-warm components or parallel initialization where possible
  - Add startup progress indicators for better UX
- **Files to Profile**:
  - `backend/detection/main.py` - Main startup sequence
  - `backend/detection/multi_region_detector.py` - MediaPipe initialization
  - `backend/detection/camera_utils.py` - Camera setup
  - `backend/server/websocket_server.py` - WebSocket startup
  - `frontend/ui/main.js` - Frontend startup coordination

**PRIORITY 3: Privacy & Performance Optimization** ✅ **NEW USER REQUEST**
- Add option to run detection without showing live camera feed
- Implement "Privacy Mode" toggle that hides video but keeps detection active
- Video quality settings (High/Medium/Low/Off) for performance optimization
- Allow algorithm to work in background without displaying user's face
- Consider showing detection status overlay without actual camera feed
- Enable completely headless detection mode for maximum privacy

**PRIORITY 2: Resource Usage Optimization & Testing**
- Implement video quality controls (resolution/frame rate reduction)
- Test system resource usage (CPU, Memory, Battery) across different modes:
  - High quality video feed
  - Medium quality video feed  
  - Low quality video feed
  - No video feed (detection only)
- Performance benchmarking tools for resource monitoring
- Lightweight mode for low-end hardware or battery preservation
- Real-time resource usage display in UI for user awareness

**PRIORITY 3: Enhanced Privacy Options**
- Option to disable camera feed recording/display entirely
- Background-only detection with minimal visual feedback
- Audio-only alerts without any visual camera component
- Stealth mode for workplace/public environments
- Camera indicator control (show/hide camera usage)

### 📋 Short-term Goals (1-2 weeks)

1. **Privacy-First Detection Mode** ✅ **HIGH PRIORITY**
   - Privacy mode toggle in UI (show/hide camera feed)
   - Video quality selector (High/Medium/Low/Off) in settings
   - Detection algorithm continues running without video display
   - Minimal status indicators without showing face
   - Background detection with audio alerts only
   - Camera usage discretion for workplace environments

2. **Enhanced User Experience**
   ✅ Sound alerts with customizable options (Chime, Beep, Gentle)
   ✅ Notification delay system (0-10 seconds) to prevent spam
   ✅ Positive reinforcement for mindful stops
   ✅ Fixed analytics counting (only actual alerts, not rapid triggers)
   - Settings persistence to local storage
   - Session history tracking
   - Volume of sounds

3. **Advanced Detection Features**
   - User-configurable sensitivity settings per region
   - Customizable region definitions and boundaries
   - Detection confidence levels display
   - Export session data to CSV/JSON
   - Ensure if user tilts head, that the polygon will be tilted as well, detection doesn't work very well when head is tilted.
   - After a while of running the app, the triggers work but sound is not audible.


### 🔮 Medium-term Goals (1-2 months)

1. **Advanced Features**
   - Historical tracking and analytics with charts
   - Export session data to CSV/JSON
   - Habit formation insights and progress tracking
   - Custom alert patterns and schedules

2. **Performance & Polish**
   ✅ **RESEARCH PRIORITY**: Video quality impact testing
   - Frame rate optimization for different hardware  
   - Memory usage improvements and monitoring
   - CPU usage optimization based on video quality settings
   - Battery usage optimization for laptops (critical for portable use)
   - Resource usage benchmarking across quality modes
   - Error handling and recovery mechanisms
   - Performance profiling tools integration

3. **Platform Expansion**
   - System tray integration for background operation
   - Auto-start with system boot option
   - Cross-platform distribution and packaging


## Technical Debt & Improvements

1. **Code Quality**
   - Add type hints throughout Python codebase
   - Implement comprehensive error handling
   - Add logging framework with proper levels
   - Code documentation and docstrings

2. **Testing & Performance Research**
   - Increase test coverage to >90%
   - Add end-to-end tests for full user workflows
   ✅ **NEW**: Performance benchmarking tests across video quality modes
   ✅ **NEW**: Resource usage testing (CPU/Memory/Battery) for optimization
   - Cross-platform compatibility tests
   - Automated performance regression testing
   - Real-world usage pattern testing for resource consumption

3. **DevOps**
   - GitHub Actions CI/CD pipeline optimization with matrix builds
   - Automated releases and distribution with proper code signing
   - Fix Windows icon format issue (RC2175 error)
   - Fix macOS backend bundling for production builds
   - Docker containerization for development
   - Code quality checks and automated formatting

## Troubleshooting

### Common Issues

1. **Camera Access Problems**
   - Ensure camera permissions are granted
   - Check if another application is using the camera
   - Try different camera indices (0, 1, 2)

2. **WebSocket Connection Failures**
   - Verify backend is running on localhost:8765
   - Check firewall settings
   - Ensure no port conflicts

3. **Tauri Build Issues**
   - Update Rust toolchain: `rustup update`
   - Clear build cache: `cargo clean`
   - Check system dependencies

4. **Production Build Issues**
   - **macOS**: Python backend not found after unsigned app installation
     - Backend bundling issue - Python executable not included in app bundle
     - Workaround: Run `xattr -c "/path/to/app"` to remove quarantine attributes
   - **Windows**: RC2175 icon format error during build
     - Icon file not in proper 3.00 format for Windows Resource Compiler
   - **Code Signing**: Apps require signing for proper distribution

### Debug Commands

```bash
# Test backend manually
uv run python -m backend.detection.main --headless

# Debug frontend-backend integration
uv run python scripts/debug_frontend.py

# Test WebSocket connection
uv run python scripts/test_websocket_integration.py

# Check system compatibility
uv run python scripts/test_mock_camera.py
```

## Contributing

1. Follow Python PEP 8 style guide
2. Run `uv run ruff format .` and `uv run ruff check --fix .` before committing
3. Add tests for new features
4. Update documentation for API changes
5. Test on multiple platforms when possible

---

*Last updated: 2025-01-22*
*Status: Core System Complete - Ready for UI Enhancement*