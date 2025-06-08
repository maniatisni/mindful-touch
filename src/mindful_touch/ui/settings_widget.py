"""Settings widget for the GUI."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QCheckBox, QLineEdit, QGroupBox
from PySide6.QtCore import Qt, Signal

from ..config import AppConfig


class SettingsWidget(QWidget):
    """Widget for configuring application settings."""

    settings_changed = Signal()

    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """Setup the settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Detection settings
        self.create_detection_settings(layout)

        # Notification settings
        self.create_notification_settings(layout)

    def create_detection_settings(self, layout):
        """Create detection settings section."""
        detection_group = QGroupBox("Detection Settings")
        detection_layout = QVBoxLayout(detection_group)

        # Sensitivity
        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(QLabel("Sensitivity:"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 100)  # 0.1 to 1.0
        self.sensitivity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sensitivity_slider.setTickInterval(10)
        sensitivity_layout.addWidget(self.sensitivity_slider)
        self.sensitivity_value = QLabel("0.7")
        self.sensitivity_value.setMinimumWidth(30)
        sensitivity_layout.addWidget(self.sensitivity_value)
        self.sensitivity_slider.valueChanged.connect(self.update_sensitivity_label)
        detection_layout.addLayout(sensitivity_layout)

        # Hand-face threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Hand-Face Distance (cm):"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(2, 50)
        self.threshold_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.threshold_slider.setTickInterval(5)
        threshold_layout.addWidget(self.threshold_slider)
        self.threshold_value = QLabel("15")
        self.threshold_value.setMinimumWidth(30)
        threshold_layout.addWidget(self.threshold_value)
        self.threshold_slider.valueChanged.connect(self.update_threshold_label)
        detection_layout.addLayout(threshold_layout)

        # Confidence threshold
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("Confidence Threshold:"))
        self.confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.confidence_slider.setRange(30, 95)  # 0.3 to 0.95
        self.confidence_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.confidence_slider.setTickInterval(10)
        confidence_layout.addWidget(self.confidence_slider)
        self.confidence_value = QLabel("0.6")
        self.confidence_value.setMinimumWidth(30)
        confidence_layout.addWidget(self.confidence_value)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        detection_layout.addLayout(confidence_layout)

        # Alert delay
        alert_delay_layout = QHBoxLayout()
        alert_delay_layout.addWidget(QLabel("Alert Delay (s):"))
        self.alert_delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.alert_delay_slider.setRange(0, 50)  # 0.0 to 5.0 seconds (step 0.1)
        self.alert_delay_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.alert_delay_slider.setTickInterval(5)
        alert_delay_layout.addWidget(self.alert_delay_slider)
        self.alert_delay_value = QLabel("0.5")
        self.alert_delay_value.setMinimumWidth(30)
        alert_delay_layout.addWidget(self.alert_delay_value)
        self.alert_delay_slider.valueChanged.connect(self.update_alert_delay_label)
        detection_layout.addLayout(alert_delay_layout)

        layout.addWidget(detection_group)

    def create_notification_settings(self, layout):
        """Create notification settings section."""
        notification_group = QGroupBox("Notification Settings")
        notification_layout = QVBoxLayout(notification_group)

        # Enable notifications
        self.notifications_enabled = QCheckBox("Enable Notifications")
        self.notifications_enabled.stateChanged.connect(self.settings_changed)
        notification_layout.addWidget(self.notifications_enabled)

        # Notification message
        message_layout = QHBoxLayout()
        message_layout.addWidget(QLabel("Message:"))
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter notification message...")
        self.message_input.textChanged.connect(self.settings_changed)
        message_layout.addWidget(self.message_input)
        notification_layout.addLayout(message_layout)

        # Cooldown period
        cooldown_layout = QHBoxLayout()
        cooldown_layout.addWidget(QLabel("Cooldown (seconds):"))
        self.cooldown_slider = QSlider(Qt.Orientation.Horizontal)
        self.cooldown_slider.setRange(0, 60)
        self.cooldown_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.cooldown_slider.setTickInterval(2)
        cooldown_layout.addWidget(self.cooldown_slider)
        self.cooldown_value = QLabel("10")
        self.cooldown_value.setMinimumWidth(30)
        cooldown_layout.addWidget(self.cooldown_value)
        self.cooldown_slider.valueChanged.connect(self.update_cooldown_label)
        notification_layout.addLayout(cooldown_layout)

        layout.addWidget(notification_group)

    def load_config(self):
        """Load configuration values into UI elements."""
        # Detection settings
        self.sensitivity_slider.setValue(int(self.config.detection.sensitivity * 100))
        self.threshold_slider.setValue(int(self.config.detection.hand_face_threshold_cm))
        self.confidence_slider.setValue(int(self.config.detection.confidence_threshold * 100))
        self.alert_delay_slider.setValue(int(self.config.detection.alert_delay_seconds * 10))

        # Notification settings
        self.notifications_enabled.setChecked(self.config.notifications.enabled)
        self.message_input.setText(self.config.notifications.message)
        self.cooldown_slider.setValue(self.config.notifications.cooldown_seconds)

        # Update labels
        self.update_sensitivity_label(self.sensitivity_slider.value())
        self.update_threshold_label(self.threshold_slider.value())
        self.update_confidence_label(self.confidence_slider.value())
        self.update_cooldown_label(self.cooldown_slider.value())
        self.update_alert_delay_label(self.alert_delay_slider.value())

    def update_sensitivity_label(self, value):
        """Update sensitivity label and config."""
        sens_value = value / 100.0
        self.sensitivity_value.setText(f"{sens_value:.1f}")
        self.config.detection.sensitivity = sens_value
        self.settings_changed.emit()

    def update_threshold_label(self, value):
        """Update threshold label and config."""
        self.threshold_value.setText(f"{value}")
        self.config.detection.hand_face_threshold_cm = float(value)
        self.settings_changed.emit()

    def update_confidence_label(self, value):
        """Update confidence label and config."""
        conf_value = value / 100.0
        self.confidence_value.setText(f"{conf_value:.1f}")
        self.config.detection.confidence_threshold = conf_value
        self.settings_changed.emit()

    def update_cooldown_label(self, value):
        """Update cooldown label and config."""
        self.cooldown_value.setText(f"{value}")
        self.config.notifications.cooldown_seconds = value
        self.settings_changed.emit()

    def update_alert_delay_label(self, value):
        """Update alert delay label and config."""
        delay_value = value / 10.0
        self.alert_delay_value.setText(f"{delay_value:.1f}")
        self.config.detection.alert_delay_seconds = delay_value
        self.settings_changed.emit()

    def update_config_from_ui(self):
        """Update configuration from UI values."""
        self.config.notifications.enabled = self.notifications_enabled.isChecked()
        self.config.notifications.message = self.message_input.text()
        self.config.detection.alert_delay_seconds = self.alert_delay_slider.value() / 10.0
