# PyQt Migration Plan - Mindful Touch

## Phase 1: Foundation Setup

### 1.1 Dependencies & Environment
- [ ] Install PyQt6 via `uv sync`
- [ ] Create main application entry point (`mindful_touch_gui.py`)
- [ ] Set up basic PyQt6 application structure
- [ ] Test GUI framework initialization

### 1.2 Project Structure
```
backend/
├── detection/          # Existing detection engine (keep as-is)
├── gui/               # New PyQt GUI package
│   ├── __init__.py
│   ├── main_window.py  # Main application window
│   ├── widgets/        # Custom widgets
│   │   ├── __init__.py
│   │   ├── detection_controls.py
│   │   ├── camera_display.py
│   │   ├── analytics_panel.py
│   │   └── custom_toggle.py
│   ├── styles/         # QSS stylesheets
│   │   ├── __init__.py
│   │   └── modern_theme.qss
│   └── resources/      # Icons, sounds, etc.
└── audio/             # Audio system
    ├── __init__.py
    └── sound_generator.py
```

## Phase 2: Core GUI Components

### 2.1 Main Window Layout
- [ ] Create `QMainWindow` with header + main grid layout
- [ ] Header: Logo + title + connection status
- [ ] Main grid: 3-panel layout (Controls | Camera + Analytics)
- [ ] Implement modern glass-morphism styling with QSS

### 2.2 Detection Controls Panel
- [ ] Custom toggle switch widget (`CustomToggle`)
- [ ] 5 region toggles: Scalp (default on), Eyebrows, Eyes, Mouth, Beard
- [ ] Notification settings section:
  - [ ] Enable notifications toggle
  - [ ] Sound alerts toggle
  - [ ] Alert delay slider (0-10 seconds) with value display
  - [ ] Sound selection buttons (Chime, Beep, Gentle)
  - [ ] Test sound button

### 2.3 Camera Display Panel
- [ ] Live camera feed display using `QLabel` with `QPixmap`
- [ ] Detection status overlay with real-time updates
- [ ] Start/Stop detection button
- [ ] Visual alert flash effect (red background)
- [ ] Fixed-width status text to prevent UI jumping

### 2.4 Analytics Panel
- [ ] Statistics display: session timer, detections, mindful stops
- [ ] Real-time counter updates
- [ ] Modern card-style layout with gradient backgrounds

## Phase 3: Detection Integration

### 3.1 Detection Engine Integration
- [ ] Direct import of `MultiRegionDetector` (no WebSocket needed)
- [ ] Create detection worker thread (`QThread`) for camera processing
- [ ] Implement Qt signals/slots for detection data communication
- [ ] Region toggle state management

### 3.2 Camera System
- [ ] OpenCV integration with PyQt (`cv2` → `QPixmap` conversion)
- [ ] Real-time frame display in GUI
- [ ] Camera permission handling
- [ ] Graceful camera errors and fallback to mock camera

### 3.3 Detection Data Flow
```python
# Signal/Slot Architecture
class DetectionWorker(QThread):
    detection_data = pyqtSignal(dict)  # Emits detection results
    frame_ready = pyqtSignal(np.ndarray)  # Emits camera frames
    
class MainWindow(QMainWindow):
    def __init__(self):
        self.detection_worker.detection_data.connect(self.on_detection_data)
        self.detection_worker.frame_ready.connect(self.update_camera_display)
```

## Phase 4: Audio System (macOS Priority)

### 4.1 macOS System Sound Integration
- [ ] **PRIMARY**: Use `NSSound` via `AppKit` for macOS system sounds
- [ ] **CRITICAL**: Avoid custom audio generation to prevent audio shutdown issues
- [ ] Use system sound names: `NSSound.soundNamed_("Ping")`, `NSSound.soundNamed_("Pop")`, `NSSound.soundNamed_("Purr")`
- [ ] Fallback to `os.system("afplay /System/Library/Sounds/...")` for system sounds
- [ ] Test long-running app audio persistence (known macOS issue with custom audio)

### 4.2 Sound Selection Mapping
- [ ] **Chime** → `"Ping"` system sound or `/System/Library/Sounds/Ping.aiff`
- [ ] **Beep** → `"Pop"` system sound or `/System/Library/Sounds/Pop.aiff` 
- [ ] **Gentle** → `"Purr"` system sound or `/System/Library/Sounds/Purr.aiff`
- [ ] Test sound button uses same system sound calls
- [ ] No custom audio buffer generation (causes shutdown issues)

## Phase 5: Features & Polish

### 5.1 Alert System
- [ ] Alert delay management (timeouts before triggering)
- [ ] Visual notifications (toast-style popups)
- [ ] Mindful stops counting (positive reinforcement)
- [ ] Statistics tracking and persistence

### 5.2 Settings & Persistence
- [ ] Save/load user preferences (`QSettings`)
- [ ] Region toggle states
- [ ] Notification preferences
- [ ] Window size/position memory

### 5.3 Visual Polish
- [ ] Modern QSS styling matching Tauri design
- [ ] Gradient backgrounds (`#667eea` to `#764ba2`)
- [ ] Glass-morphism panels (transparency + blur effects)
- [ ] Smooth animations and transitions
- [ ] Responsive layout for different screen sizes

## Phase 6: System Integration

### 6.1 Application Lifecycle
- [ ] System tray integration for background operation
- [ ] Auto-start with system option
- [ ] Proper application quit handling
- [ ] Memory cleanup and resource management

### 6.2 Cross-Platform Considerations
- [ ] macOS: Menu bar integration, camera permissions
- [ ] Windows: Taskbar integration, camera permissions
- [ ] Application icons and system integration

## Phase 7: Build & Distribution

### 7.1 PyInstaller Configuration
- [ ] Create new PyInstaller spec for PyQt application
- [ ] Bundle all resources (icons, sounds, stylesheets)
- [ ] Handle PyQt6 dependencies and Qt plugins
- [ ] Test standalone executable

### 7.2 Platform-Specific Builds
- [ ] macOS: Create `.app` bundle with proper Info.plist
- [ ] Windows: Create `.exe` with proper icons and metadata
- [ ] Code signing for distribution (optional)

## Implementation Priority

### Critical Path (MVP):
1. **Main window + basic layout** (Phase 2.1)
2. **Detection controls** (Phase 2.2)
3. **Camera display** (Phase 2.3)
4. **Detection integration** (Phase 3.1-3.3)
5. **Basic audio** (Phase 4.1)
6. **PyInstaller build** (Phase 7.1)

### Enhancement Phase:
- Advanced styling and animations
- System tray integration
- Settings persistence
- Cross-platform optimizations

## Technical Notes

### Key Qt Classes to Use:
- `QMainWindow`: Main application window
- `QGridLayout`: Main layout system
- `QThread`: Detection worker thread
- `QTimer`: Session timer, alert delays
- `QLabel`: Camera display, status indicators
- `QSlider`: Alert delay setting
- `QPushButton`: Toggle buttons, test sound
- `QSoundEffect`: Audio playback
- `QSettings`: Preferences storage

### Signal/Slot Communication:
```python
# Replace WebSocket messages with Qt signals
detection_data_received = pyqtSignal(dict)
region_toggle_changed = pyqtSignal(str, bool)
alert_triggered = pyqtSignal(list)
```

### Styling Strategy:
- Use QSS (Qt Style Sheets) for modern appearance
- Implement custom widgets for complex components
- Maintain consistent color scheme and typography
- Support high-DPI displays

## Success Criteria

- [ ] All Tauri UI features replicated in PyQt
- [ ] Detection engine works identically
- [ ] Single executable builds successfully
- [ ] No WebSocket/process management complexity
- [ ] Maintains visual design quality
- [ ] Cross-platform compatibility (macOS + Windows)

## DETAILED UI SPECIFICATIONS (From Tauri Analysis)

### Window Layout Structure
```
┌─────────────────────────────────────────────────────────────────┐
│ HEADER: Logo + "Mindful Touch" + Connection Status             │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────────────────────────────┐ │
│ │ CONTROLS PANEL  │ │ CAMERA PANEL                            │ │
│ │                 │ │ Live Detection                          │ │
│ │ Detection       │ │ ┌─────────────────────────────────────┐ │ │
│ │ Regions         │ │ │ Camera Feed / Placeholder           │ │ │
│ │ ├ Scalp ✓       │ │ │ + Detection Overlay                 │ │ │
│ │ ├ Eyebrows ✗    │ │ │ + Start/Stop Button                 │ │ │
│ │ ├ Eyes ✗        │ │ └─────────────────────────────────────┘ │ │
│ │ ├ Mouth ✗       │ ├─────────────────────────────────────────┤ │
│ │ ├ Beard ✗       │ │ ANALYTICS PANEL                         │ │
│ │                 │ │ Today's Activity                        │ │
│ │ Notification    │ │ ┌─────┐ ┌─────┐ ┌─────┐                │ │
│ │ Settings        │ │ │  0  │ │ 0m  │ │  0  │                │ │
│ │ ├ Enable ✓      │ │ │Det. │ │Sess.│ │Stop │                │ │
│ │ ├ Sound ✓       │ │ └─────┘ └─────┘ └─────┘                │ │
│ │ ├ Delay: 3s     │ │                                         │ │
│ │ ├ [🔔][📢][🎵] │ │                                         │ │
│ │ └ ▶️ Test       │ │                                         │ │
│ └─────────────────┘ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Exact Color Specifications
```css
/* Primary Colors */
--primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--accent-color: #667eea
--success-color: #10b981
--error-color: #ef4444
--text-primary: #4a5568
--text-secondary: #718096

/* Background Colors */
--body-bg: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--panel-bg: rgba(255, 255, 255, 0.95)
--panel-border: rgba(255, 255, 255, 0.2)
--hover-bg: rgba(102, 126, 234, 0.05)

/* Component Colors */
--toggle-off: #cbd5e0
--toggle-on: #667eea
--slider-track: #cbd5e0
--slider-thumb: #667eea
--button-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
--button-success: #10b981
--button-error: #ef4444
```

### Typography Specifications
```css
--font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
--font-size-h1: 1.5rem (24px)
--font-size-h2: 1.25rem (20px) 
--font-size-body: 0.875rem (14px)
--font-size-small: 0.75rem (12px)
--font-weight-normal: 500
--font-weight-semibold: 600
--font-weight-bold: 700
```

### Component Specifications

#### Header (QWidget)
- Height: ~80px
- Background: `rgba(255, 255, 255, 0.95)` + backdrop blur
- Logo: 40x40px rounded (8px border-radius)
- Title: "Mindful Touch" (24px, semibold, #4a5568)
- Status: Pill shape (20px border-radius), "Connected"/"Offline"

#### Custom Toggle Switch (QWidget)
- Size: 50px × 24px
- Border radius: 24px (fully rounded)
- Off state: Background #cbd5e0
- On state: Background #667eea
- Knob: 18px × 18px white circle, 3px margin, drop shadow
- Animation: 0.3s ease transition

#### Region Controls Section
- 5 toggles: Scalp (default ON), Eyebrows, Eyes, Mouth, Beard (default OFF)
- Layout: Vertical stack, 1rem gap
- Each row: Toggle + Label, 0.75rem padding, hover effect
- Hover: Background `rgba(102, 126, 234, 0.05)`

#### Notification Settings Section
- Enable/Sound toggles (same style as region toggles)
- Delay slider: 
  - Width: 100%
  - Height: 6px track
  - Thumb: 20px circle #667eea
  - Value display: "3s" (semibold, #667eea)
- Sound buttons:
  - 3 buttons: "🔔 Chime", "📢 Beep", "🎵 Gentle"
  - Default: Chime active
  - Style: 2px border, white bg, rounded 8px
  - Active: #667eea background, white text
  - Hover: border #667eea, slight transform up
- Test button: Green (#10b981) border, transparent bg

#### Camera Panel
- Background: #f7fafc for placeholder area
- Min height: 300px
- Placeholder state:
  - Icon: 📹 (3rem font size, 50% opacity)
  - Text: "Camera feed will appear here"
  - Button: Primary gradient, 140px width, "Start Detection"
- Active state:
  - Live camera feed (QLabel with QPixmap)
  - Detection overlay: Fixed position (10px from top-left)
  - Overlay size: 220px × fixed height
  - Overlay: Black 80% opacity, white text, monospace font
  - Status indicators: Fixed width to prevent jumping

#### Analytics Panel
- 3 stat cards in grid layout
- Card style: Primary gradient background, white text
- Padding: 1.5rem
- Border radius: 12px
- Numbers: 2rem font, bold (700 weight)
- Labels: 0.875rem font, 90% opacity

#### Detection Overlay Specifications
```
Overlay Contents:
┌─────────────────────────┐
│ Hands: Detected ✓       │ ← Fixed width 120px
│ Face: Not detected ✗    │ ← Fixed width 120px  
│ Contacts: 0             │ ← Green/red based on count
│ No alerts               │ ← Alert status
│ [Stop Detection]        │ ← 110px width button
└─────────────────────────┘
```

#### Visual Effects
- Glass morphism: `backdrop-filter: blur(10px)` equivalent
- Box shadows: `0 8px 32px rgba(0, 0, 0, 0.1)`
- Button hover: `transform: translateY(-2px)` + shadow increase
- Alert flash: Background changes to `rgba(239, 68, 68, 0.9)` for 200ms
- Smooth transitions: 0.2s ease for hover effects, 0.3s for toggles

#### Responsive Breakpoints
- Desktop: Grid layout (2 columns)
- Mobile (<768px): Single column, stacked panels

### macOS-Specific Requirements
- Use native macOS system sounds (`Ping`, `Pop`, `Purr`)
- Handle camera permissions gracefully
- Support system menu bar integration
- Retina display compatibility (high DPI)
- Native window controls and behavior

---

**Estimated Timeline:** 2-3 development sessions
**Risk Mitigation:** Incremental testing, system sound fallbacks for audio reliability
**Performance Goal:** Eliminate Tauri startup delays and process coordination issues
**Priority:** macOS system sound integration to prevent audio shutdown issues