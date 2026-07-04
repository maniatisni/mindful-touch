# Mindful Touch

A gentle awareness tool for mindful hand movement tracking.

<p align="center">
  <img src="logo.png" width="150" title="Mindful Touch">
</p>

Mindful Touch helps you become more aware of unconscious face-touching habits. Using your webcam, it tracks your hands and face in real time and plays a gentle sound when a hand lingers on a facial region — scalp, eyebrows, eyes, mouth, or beard area. Brief, intentional touches are recognized as "mindful stops" and celebrated instead of alerted.

All processing happens locally on your device. Nothing is recorded, collected, or transmitted.

## Features

- **Multi-region detection** — monitor scalp, eyebrows, eyes, mouth, and beard area independently
- **Configurable alert delay** — choose how long a touch must last before the alert sounds
- **Mindful stops** — pulling your hand away before the alert fires counts as a win, not a failure
- **Privacy mode** — hide the camera feed while detection keeps running in the background
- **Session statistics** — detections, session duration, and mindful stops at a glance
- **Settings persistence** — your region choices and alert delay are remembered between sessions
- **Local-only** — no accounts, no telemetry, no network access

## Requirements

- **For releases**: just download the DMG from the [Releases](../../releases) page (macOS)
- **For development**: Python 3.9+, [UV](https://docs.astral.sh/uv/) package manager
- **Hardware**: webcam (built-in or external)

## Installation

### From a release (recommended)

1. Download the latest `Mindful-Touch-*.dmg` from the [Releases](../../releases) page
2. Open the DMG and drag **Mindful Touch** into **Applications**
3. On first launch, macOS may block the unsigned app — right-click the app and choose **Open**, or run:
   ```bash
   xattr -c "/Applications/Mindful Touch.app"
   ```
4. Grant camera access when prompted (System Settings → Privacy & Security → Camera)

### From source

```bash
# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and set up
git clone https://github.com/maniatisni/mindful-touch.git
cd mindful-touch
uv sync

# Run the app
uv run python main.py
```

## Development

```bash
# Lint and format
uv run ruff check . && uv run ruff format .

# Run tests
uv run pytest

# Build a standalone .app (macOS)
uv run pyinstaller mindful-touch.spec --clean --noconfirm
open "dist/Mindful Touch.app"
```

Releases are built automatically by GitHub Actions when a `v*` tag is pushed.

## Architecture

A single-process PyQt6 desktop app:

- `main.py` — application entry point; the main window and a camera `QThread`
- `backend/detection/multi_region_detector.py` — MediaPipe face-mesh + hand tracking, region polygons, temporal filtering
- `backend/detection/config.py` — detection tuning constants
- `backend/detection/settings_store.py` — JSON settings persistence (`~/.mindful-touch/settings.json`)
- `ui/` — panels, widgets, and theme

## License

MIT — see [LICENSE](LICENSE).
