# Mindful Touch

A gentle awareness tool for mindful hand movement tracking.

<p align="center">
  <img src="logo.png" width="150" title="Mindful Touch">
</p>

Mindful Touch helps you become more aware of unconscious face-touching habits by providing gentle, non-intrusive notifications when your hands approach specific facial regions. The application uses advanced multi-region detection to identify contact with areas like the scalp, eyebrows, eyes, mouth, and beard area.

## 🌟 Features

- **Multi-region detection**: Monitors specific facial regions (scalp, eyebrows, eyes, mouth, beard)
- **Real-time visualization**: Live camera feed with detection overlays
- **Privacy-first**: All processing happens locally on your device
- **Lightweight**: Minimal dependencies and system resource usage

## 📋 Requirements

- Python 3.8 or newer
- Webcam
- Operating System: Windows, macOS, or Linux

## 🔧 Installation

### Step 1: Install UV (recommended)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (pip):**
```bash
pip install uv
```

### Step 2: Clone and setup

```bash
# Clone the repository
git clone https://github.com/maniatisni/mindful-touch.git
cd mindful-touch

# Install dependencies
uv sync

# Install the application
uv pip install -e .
```

## 🚀 Quick Start

### Run with UV (recommended)
```bash
uv run mindful-touch
```

### Alternative methods
```bash
# Run as module
uv run python -m mindful_touch

# If installed globally
mindful-touch
```

## 🎮 Usage

When the application starts, you'll see:
1. **Live camera feed** with detection visualization
2. **Status overlay** showing detection information
3. **Region boundaries** drawn around active detection areas

## 🛠️ Development

### Running linting and code checks
```bash
# Check code quality
uv run ruff check src/

# Auto-fix issues
uv run ruff check src/ --fix
```

## 🔍 Troubleshooting

### Camera Issues
- **No camera detected**: Ensure your webcam is connected and not used by other applications
- **Poor detection**: Ensure good lighting and position camera at eye level
- **Permission errors**: Grant camera permissions to your terminal/application

### Performance Issues
- **High CPU usage**: Close other camera applications
- **Slow detection**: Ensure adequate lighting for better MediaPipe performance

### Common Solutions
```bash
# Reinstall dependencies
uv sync --reinstall

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