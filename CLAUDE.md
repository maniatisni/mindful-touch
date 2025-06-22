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
   cd frontend
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
cd frontend
cargo tauri build
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

### 🚧 Current Issues

1. **WebSocket Connection Problem**
   - Frontend shows "connected" initially but fails to maintain connection
   - Backend process management issues in Tauri
   - WebSocket connection timing problems
   - Process lifecycle not properly handled

### 🔄 In Progress

1. **Process Management Fixes**
   - Enhanced Tauri backend process spawning
   - Added proper process cleanup and shutdown
   - Improved error handling and logging
   - Better path resolution for different deployment contexts

## Next Steps & Roadmap

### 🎯 Immediate Priorities (Critical)

1. **Fix WebSocket Connection**
   - Debug backend process startup in Tauri context
   - Resolve WebSocket server initialization timing
   - Implement proper process health checks
   - Add connection retry mechanisms

2. **Backend Process Stability**
   - Ensure Python backend stays running when launched from Tauri
   - Add process monitoring and automatic restart
   - Improve error reporting from backend to frontend

### 📋 Short-term Goals (1-2 weeks)

1. **Enhanced UI/UX**
   - Add live camera feed display in frontend
   - Implement visual feedback for detected contacts
   - Add sound notifications for alerts
   - Improve statistics dashboard

2. **Configuration & Settings**
   - User-configurable sensitivity settings
   - Customizable region definitions
   - Settings persistence
   - Theme customization

3. **Performance Optimization**
   - Frame rate optimization
   - Memory usage improvements  
   - CPU usage monitoring
   - Battery usage optimization for laptops

### 🔮 Medium-term Goals (1-2 months)

1. **Advanced Features**
   - Historical tracking and analytics
   - Export data to CSV/JSON
   - Habit formation insights
   - Custom alert patterns

2. **Platform Expansion**
   - Mobile app version (React Native or Flutter)
   - Web-based version for browsers
   - System tray integration


## Technical Debt & Improvements

1. **Code Quality**
   - Add type hints throughout Python codebase
   - Implement comprehensive error handling
   - Add logging framework with proper levels
   - Code documentation and docstrings

2. **Testing**
   - Increase test coverage to >90%
   - Add end-to-end tests for full user workflows
   - Performance benchmarking tests
   - Cross-platform compatibility tests

3. **DevOps**
   - GitHub Actions CI/CD pipeline
   - Automated releases and distribution
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
*Status: Active Development - WebSocket Integration Phase*