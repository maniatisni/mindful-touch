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

### 🔧 CURRENT SESSION STATUS (June 25, 2025)

**BRANCH**: `fix/production-builds` (ahead of origin by commits)
**TAG**: `v1.0.0-test` (triggers GitHub Actions build on push)

**CRITICAL ISSUE IN PROGRESS: macOS Backend Executable Not Found**

**Problem**: Built macOS app shows error: "Failed to start detection: Failed to start backend. Standalone executable not found and development environment not available."

**Root Cause Analysis**:
1. ✅ GitHub Actions builds PyInstaller executable successfully
2. ✅ Copies `mindful-touch-backend` to `frontend/src-tauri/resources/`
3. ❌ Tauri app cannot find the executable at runtime
4. ❌ Rust code resource path resolution failing

**Current State**: 
- PyInstaller spec file: `backend_standalone.spec` ✅ (removed from .gitignore)
- GitHub Actions workflow: Fixed Windows PowerShell syntax ✅
- Tauri config: Resources point to `resources/*` ✅
- Rust backend detection: Looks in `resource_dir()` first ✅

**IMMEDIATE NEXT STEPS**:
1. **Debug macOS Resource Path**: Add logging to Rust code to see actual resource directory path
2. **Verify Bundle Structure**: Check if backend executable is actually included in .app bundle
3. **Fix Resource Resolution**: Ensure Tauri properly bundles the executable in the correct location
4. **Test Path Variations**: Try different resource path patterns for macOS

**TO CONTINUE DEVELOPMENT**:
```bash
# Switch to working branch
git checkout fix/production-builds

# To retrigger GitHub Actions build:
git tag -d v1.0.0-test
git push origin :refs/tags/v1.0.0-test
git tag v1.0.0-test
git push origin v1.0.0-test

# OR push any new commits to trigger build via branch
git push origin fix/production-builds
```

**FILES MODIFIED IN THIS SESSION**:
- `.github/workflows/tag-release.yml`: Fixed PyInstaller integration + Windows PowerShell syntax
- `.gitignore`: Removed `*.spec` exclusions  
- `backend_standalone.spec`: PyInstaller configuration ✅
- `backend_entry.py`: Standalone entry point ✅
- `frontend/src-tauri/tauri.conf.json`: Resource bundling config
- `frontend/src-tauri/src/main.rs`: Enhanced backend path resolution

**DEBUGGING PLAN**:
1. Add debug logging to Rust backend detection code
2. Inspect actual .app bundle contents manually
3. Test different resource path patterns
4. Verify executable permissions in bundle
5. Consider alternative bundling approaches if needed

### 🔧 NEXT SESSION PRIORITIES (Production Release Issues)

**CRITICAL PRIORITY 1: Fix macOS Backend Executable Resolution** ⚠️ **IN PROGRESS**
- Debug why Tauri resource_dir() doesn't contain the backend executable
- Verify PyInstaller executable is properly bundled in macOS .app
- Fix Rust path resolution for production vs development
- Test different resource bundling configurations

**CRITICAL PRIORITY 2: Complete Production Build Pipeline**
- **Windows Build**: Verify executable bundling works correctly
- **Linux Build**: Test AppImage/Deb packaging with backend
- **Code Signing**: Implement proper code signing for macOS distribution
- **CI/CD Validation**: Add automated testing for production builds

**CRITICAL PRIORITY 3: Cross-Platform Validation**
- Validate backend process management on all platforms in production
- Ensure proper error handling when Python backend fails to start
- Test resource usage and performance in production builds
- Add comprehensive logging for debugging distribution issues

### 🎯 Immediate Next Tasks (After Build Issues Resolved)

**PRIORITY 1: Privacy & Performance Optimization** ✅ **NEW USER REQUEST**
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