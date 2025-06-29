# Mindful Touch

A gentle awareness tool for mindful hand movement tracking.

<p align="center">
  <img src="logo.png" width="150" title="Mindful Touch">
</p>

Mindful Touch helps you become more aware of unconscious face-touching habits by providing gentle, non-intrusive notifications when your hands approach specific facial regions. The application uses advanced multi-region detection to identify contact with areas like the scalp, eyebrows, eyes, mouth, and beard area.

## 🌟 Features

- **Cross-platform desktop app**: Native desktop application built with Tauri
- **Multi-region detection**: Monitors specific facial regions (scalp, eyebrows, eyes, mouth, beard)
- **Real-time WebSocket communication**: Live data streaming between backend and frontend
- **Interactive region controls**: Toggle detection regions on/off in real-time
- **Session statistics**: Track detection events and session duration
- **Automatic backend management**: No manual backend startup required
- **Privacy-first**: All processing happens locally on your device
- **Lightweight**: Minimal system resource usage with optimized performance

## 📋 Requirements

- **For releases**: Just download and install from [GitHub Releases](../../releases)
- **For development**: Python 3.8+, Rust/Cargo, UV package manager
- **Hardware**: Webcam (built-in or external)
- **OS**: macOS (production ready), Windows (coming soon), Linux (manual build)

## 🔧 Installation

### Step 1: Install Prerequisites

**UV Package Manager:**
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative (pip)
pip install uv
```

**Tauri CLI:**
```bash
cargo install tauri-cli
```

### Step 2: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/maniatisni/mindful-touch.git
cd mindful-touch

# Install Python dependencies
uv sync
```

## 🚀 Quick Start

### Desktop Application (Recommended)
```bash
cd frontend/src-tauri
cargo tauri dev
```

### Backend Only (For Development/Testing)
```bash
# GUI mode with live video feed
uv run python -m backend.detection.main

# Headless mode (for frontend integration)
uv run python -m backend.detection.main --headless

# Mock camera mode (for CI/testing)
uv run python -m backend.detection.main --headless --mock-camera
```

## 🎮 Usage

### Desktop Application
When you launch the desktop app (`cargo tauri dev`), you'll see:
1. **Connection status** showing backend communication
2. **Region toggle controls** to enable/disable detection areas
3. **Real-time statistics** showing detection events and session time
4. **Start/Stop detection** controls for managing the detection process

The application automatically manages the Python backend - no manual startup required!

### Development Mode
For development and testing, you can run the backend separately:
1. **Live camera feed** with detection visualization
2. **Status overlay** showing detection information  
3. **Region boundaries** drawn around active detection areas
4. **WebSocket server** for real-time communication on port 8765

## 🛠️ Development

### Build for Production
```bash
cd frontend/src-tauri
cargo tauri build
```

### Installing Production Builds

**Linux (AppImage/DEB):**
- Download from [releases](../../releases)
- AppImage: `chmod +x Mindful-Touch.AppImage && ./Mindful-Touch.AppImage`
- DEB: `sudo dpkg -i mindful-touch_*.deb`

**Windows (MSI/NSIS):**
- Download from [releases](../../releases)
- Run the installer (`.msi` or `.exe`)

**macOS (DMG/APP):**
- Download from [releases](../../releases)
- Open the DMG and drag to Applications folder
- **Important**: macOS will show a security warning for unsigned apps. To allow the app:
  ```bash
  xattr -c "/Applications/Mindful Touch.app"
  ```
- Or right-click the app → "Open" → "Open" to bypass the warning
- Grant camera permission when prompted

### Running Tests
```bash
# Python tests
uv run pytest

# Integration tests
uv run python scripts/run_integration_tests.py

# Mock camera tests
uv run python scripts/test_mock_camera.py
```

### Code Quality
```bash
# Check code quality
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix

# Format code
uv run ruff format .
```

### WebSocket Testing
```bash
# Test WebSocket connection
uv run python scripts/test_websocket_integration.py

# Debug frontend-backend integration
uv run python scripts/debug_frontend.py
```

## 🔍 Troubleshooting

### Desktop Application Issues
- **Backend not starting**: Check if Python is installed and dependencies are available
- **Connection failures**: Ensure no firewall blocking localhost:8765
- **Tauri build errors**: Update Rust toolchain with `rustup update`

### Camera Issues
- **No camera detected**: Ensure your webcam is connected and not used by other applications
- **Poor detection**: Ensure good lighting and position camera at eye level
- **Permission errors**: Grant camera permissions to your terminal/application

### WebSocket Issues
- **Connection timeout**: Verify backend is running on localhost:8765
- **Data not updating**: Check WebSocket connection status in frontend
- **Port conflicts**: Ensure port 8765 is not used by other applications

### Performance Issues
- **High CPU usage**: Close other camera applications
- **Slow detection**: Ensure adequate lighting for better MediaPipe performance
- **Memory leaks**: Restart the application if running for extended periods

### Common Solutions
```bash
# Reinstall dependencies
uv sync --reinstall

# Clean build cache
cd frontend/src-tauri && cargo clean

# Update to latest version
git pull
uv sync
```

## 🔒 Privacy & Security

Mindful Touch is designed with privacy as a core principle:

- **Local processing**: All detection happens on your device
- **No data transmission**: No images or data sent to external servers
- **No storage**: By default, no images or detection data is saved
- **Camera access**: Only active when application is running

## 🧠 Mindfulness Tips

Mindful Touch works best when combined with intention:

1. **Set an intention**: Before starting, take a moment to set an intention for awareness
2. **Gentle acknowledgment**: When you see detection alerts, simply acknowledge without judgment
3. **Breathe and release**: Take a breath and gently move your hand away
4. **Notice patterns**: Over time, observe when you're most likely to touch your face

## 📜 License

Mindful Touch is released under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

---

May your mindfulness journey be gentle and insightful. 🌸