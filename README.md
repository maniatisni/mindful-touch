# Mindful Touch

A gentle awareness tool for mindful hand movement tracking.
<p align="center">
  <img src="logo.png" width="150" title="Mindful Touch">
</p>

Mindful Touch helps you become more aware of unconscious face-touching habits by providing gentle, non-intrusive notifications when your hands approach your face. By increasing awareness of these automatic movements, the application supports mindfulness practices and can help reduce the effects of habits like nail biting, trichotillomania, and others.

## 🌟 Features

- **Real-time detection**: Monitors hand-to-face proximity using your webcam
- **Gentle notifications**: Provides calm, non-judgmental reminders when your hands approach your face
- **Privacy-first**: All processing happens locally on your device - no data is sent to servers
- **Customizable**: Adjust sensitivity, thresholds, and notification settings to suit your needs
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Lightweight**: Minimal system resource usage

## 📋 Requirements

- Python 3.8 or newer
- Webcam
- Operating System: Windows, macOS, or Linux

## 🔧 Installation

### Step 1: Install UV (if not already installed)

UV is a fast Python package installer and resolver.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Clone the repository

```bash
git clone https://github.com/maniatisni/mindful-touch.git
cd mindful-touch
```

### Step 3: Install dependencies

```bash
uv sync
```

## 🚀 Quick Start

To start the application with default settings:

```bash
mindful-touch start
```

To display a live video feed showing detection status:

```bash
mindful-touch start --live-feed
```

## 🎮 Usage Guide

Mindful Touch provides several commands to help you manage and customize your experience.

### Main Commands

#### `start`: Begin monitoring

```bash
mindful-touch start [OPTIONS]
```

**Options:**
- `--live-feed`: Show real-time camera feed with visual annotations
- `--sensitivity FLOAT`: Set detection sensitivity (0.1-1.0, default 0.7)
- `--threshold FLOAT`: Set hand-face distance threshold in cm (5.0-50.0, default 15.0)

**Examples:**
```bash
# Start with increased sensitivity
mindful-touch start --sensitivity 0.9

# Start with a larger threshold distance
mindful-touch start --threshold 20

# Start with live video feed
mindful-touch start --live-feed
```


**Options:**

#### `config`: View or update configuration

```bash
mindful-touch config [OPTIONS]
```

**Options:**
- `--sensitivity FLOAT`: Set detection sensitivity (0.1-1.0)
- `--threshold FLOAT`: Set hand-face distance threshold in cm (2.0-50.0)
- `--cooldown INT`: Set notification cooldown period in seconds (5-300)
- `--camera-id INT`: Set camera device ID

**Examples:**
```bash
# Update multiple settings at once
mindful-touch config --sensitivity 0.8 --cooldown 15

# View current configuration (no parameters)
mindful-touch config
```

#### `test`: Verify camera and notifications

```bash
mindful-touch test
```

This command tests:
1. Camera connectivity
2. Desktop notification system

#### `list-cameras`: Find available cameras

```bash
mindful-touch list-cameras
```

Shows all available camera devices with their resolution and frame rate information.

## ⚙️ Configuration Parameters

Mindful Touch can be customized through the following parameters:

### Detection Settings

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `sensitivity` | Overall detection sensitivity | 0.1-1.0 | 0.7 |
| `hand_face_threshold_cm` | Distance threshold for triggering notifications (in cm) | 2.0-50.0 | 15.0 |
| `detection_interval_ms` | Time between detection checks (ms) | 50-1000 | 100 |
| `confidence_threshold` | Minimum confidence score for detection | 0.3-0.95 | 0.6 |

### Notification Settings

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `enabled` | Enable/disable notifications | boolean | true |
| `title` | Notification title | text | "Mindful Moment" |
| `message` | Notification message | text | "Take a gentle pause 🌸" |
| `duration_seconds` | Notification display time | 1-30 | 3 |
| `cooldown_seconds` | Minimum time between notifications | 5-300 | 10 |

### Camera Settings

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `device_id` | Camera device ID | 0+ | 0 |
| `width` | Camera capture width | 320-1920 | 640 |
| `height` | Camera capture height | 240-1080 | 480 |
| `fps` | Frames per second | 10-60 | 30 |

### Privacy Settings

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `save_images` | Save detection images | boolean | false |
| `log_detections` | Log detection events | boolean | false |

## 🔄 Adjusting Your Experience

### Finding the Right Sensitivity

- **Higher sensitivity** (0.8-1.0): Triggers notifications when hands are further from your face. Good for building initial awareness.
- **Medium sensitivity** (0.5-0.7): Balanced approach that works for most users.
- **Lower sensitivity** (0.1-0.4): Only notifies when hands are very close to your face. Useful once you've developed better awareness.

### Understanding the Live Feed Display

When using the `--live-feed` option, you'll see:

- **Green "Monitoring..."**: Normal operation, no hand-face proximity detected
- **Red "PULLING DETECTED!"**: Hand proximity detected
- **Distance measurement**: Current hand-face distance in centimeters


## 🧠 Mindfulness Practices

Mindful Touch works best when combined with intention:

1. **Set an intention**: Before starting, take a moment to set an intention for awareness.
2. **Gentle acknowledgment**: When you receive a notification, simply acknowledge it without self-judgment.
3. **Breathe and release**: Take a breath and gently move your hand away from your face.
4. **Notice patterns**: Over time, notice when you're most likely to touch your face (stress, concentration, etc.).

## 🔍 Troubleshooting

### Camera Issues

- **Camera not detected**: Try the `list-cameras` command to see available devices
- **Poor detection**: Ensure proper lighting and position your camera at eye level
- **Performance issues**: Lower the resolution or FPS in the configuration

### Notification Issues

- **No notifications**: Run the `tewst` command to check your notification system
- **Too many notifications**: Increase the cooldown period or reduce sensitivity
- **Too few notifications**: Increase sensitivity or decrease the threshold distance

### General Issues

- **Application crash**: Check for updates to dependencies
- **High CPU usage**: Reduce the detection frequency by increasing `detection_interval_ms`

## 🔄 Updates and Maintenance

To update Mindful Touch to the latest version:

```bash
git pull
uv sync
```

## 🔒 Privacy Information

Mindful Touch is designed with privacy as a core principle:

- All processing happens locally on your device
- No images or data are sent to any server
- By default, no data is saved to disk
- The application only uses your camera when running

## 💬 Community and Support

- **GitHub Issues**: Report bugs or suggest features
- **Email Support**: maniatisni@gmail.com

## 📜 License

Mindful Touch is released under the MIT License. See the [LICENSE](LICENSE) file for details.

---

May your mindfulness journey be gentle and insightful. 🌸
