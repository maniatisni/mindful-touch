# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mindful Touch is a trichotillomania-specific detection application that monitors hand-to-face proximity using computer vision to provide gentle notifications when users approach pulling behaviors. The application uses MediaPipe for real-time hand and face tracking, with sophisticated filtering to reduce false positives.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev
```

### Code Quality & Testing
```bash
# Run linting (auto-fix enabled)
uv run ruff check --fix src/

# Run type checking
uv run mypy src/

# Run tests
uv run pytest

# Run single test file
uv run pytest tests/test_detector.py

# Run tests with coverage
uv run pytest --cov=src/mindful_touch --cov-report=term-missing
```

### Application Execution
```bash
# Run application (installs as mindful-touch command)
uv run mindful-touch start

# Run with live video feed for debugging
uv run mindful-touch start --live-feed

# Test camera and notifications
uv run mindful-touch test

# View/modify configuration
uv run mindful-touch config

# Alternative: Run via module
uv run python -m mindful_touch.main start
```

### Jupyter Development
```bash
# Install notebook dependencies
uv sync --extra dev

# Start notebook (detection algorithm experimentation)
uv run jupyter lab notebooks/
```

## Code Architecture

### Core Detection Pipeline

The detection system follows a modular 4-stage pipeline:

1. **MediaPipe Processing** (`HandFaceDetector`): Extracts hand and face landmarks
2. **Hand Analysis** (`HandAnalyzer`): Analyzes gestures, velocity, pinch quality, palm orientation
3. **Face Region Detection** (`FaceRegionDetector`): Identifies target areas (eyebrows, scalp, temples)  
4. **Detection Filtering** (`DetectionFilter`): Applies multi-criteria filtering for final detection decision

### Key Components

**Detection Engine** (`src/mindful_touch/detector.py`):
- `DetectionConstants`: Centralized thresholds and parameters
- `GeometryCalculator`: Pure 3D math functions (vectors, angles, distances)
- `HandAnalyzer`: Velocity tracking, pinch analysis, palm orientation detection
- `FaceRegionDetector`: Face landmark processing and target region extraction
- `DetectionFilter`: Multi-criteria filtering (orientation + velocity + temporal consistency)
- `HandFaceDetector`: Main coordinator using modular components

**Configuration System** (`src/mindful_touch/config.py`):
- Pydantic-based configuration with validation
- Persistent storage in platform-specific config directories
- Separation of detection, notification, and camera settings

**Notification System** (`src/mindful_touch/notifier.py`):
- Cross-platform notifications (macOS: pync, Linux: notify-send, Windows: win10toast)
- Cooldown management and temporal filtering

**User Interface** (`src/mindful_touch/ui/`):
- Qt-based GUI with real-time detection worker
- CLI interface via Click for configuration and testing

### False Positive Reduction Strategy

The system implements multiple layers to distinguish actual pulling behavior from casual hand movements:

1. **Hand Orientation**: Palm must face target regions (calculated via cross product of hand vectors)
2. **Velocity Filtering**: Hand movement must be slow/deliberate (≤100 pixels/sec)
3. **Pinch Quality**: Thumb-index angle must be 60-120° (proper pulling grip)
4. **Temporal Consistency**: 2-second sustained detection requirement
5. **Spatial Targeting**: Different thresholds for eyebrows (closer) vs scalp/temples
6. **Cooldown Periods**: 6-second minimum between notifications

### Testing Strategy

The modular architecture enables component-level testing:

- **Unit Tests**: Each component (GeometryCalculator, HandAnalyzer, etc.) can be tested independently
- **Integration Tests**: Full pipeline testing with synthetic MediaPipe landmark data
- **Regression Tests**: Maintain detection accuracy across changes
- **Performance Tests**: Ensure real-time processing requirements

## Key Configuration Parameters

**Detection Sensitivity**:
- `sensitivity` (0.1-1.0): Overall detection sensitivity
- `hand_face_threshold_cm` (2.0-50.0): Base distance threshold
- `alert_delay_seconds` (0.0-5.0): Sustained detection requirement

**Algorithm Constants** (in `DetectionConstants`):
- `MAX_PULLING_VELOCITY_PX_PER_SEC`: Velocity threshold for filtering quick movements
- `PALM_FACING_DOT_THRESHOLD`: Dot product threshold for palm orientation
- `PINCH_ANGLE_MIN/MAX_DEGREES`: Valid pinch angle range

## Development Notes

**MediaPipe Integration**: The system processes 468 face landmarks and 21 hand landmarks per frame. Face landmarks 10, 9, 151 define the forehead center to avoid nose-touch false positives.

**Performance Considerations**: Detection runs at ~100ms intervals with adaptive timing based on processing time. The velocity history maintains only 5 frames to balance accuracy with memory usage.

**Platform-Specific Handling**: macOS requires camera permissions and uses pync for notifications. The build system includes PyInstaller hooks for MediaPipe bundling.

**Hand Laterality Issue**: There may be sensitivity differences between left/right hands in palm orientation calculations - this is a known area for investigation.

## Jupyter Notebooks

`notebooks/mindful-touch.ipynb` provides an interactive development environment for:
- Real-time detection algorithm testing
- Parameter tuning with ipywidgets
- Visual debugging of detection pipeline
- Performance profiling and FPS monitoring