"""
iOS-style Toggle Switch Widget
Smooth animated toggle for boolean settings
"""

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRect, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import QCheckBox, QWidget

from ui.styles.theme import Theme


class ToggleSwitch(QCheckBox):
    """iOS-style animated toggle switch"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 26)

        # Animation setup
        self._circle_position = 3
        self.animation = QPropertyAnimation(self, b"circle_position")
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setDuration(200)

        # Connect state change to animation
        self.stateChanged.connect(self._on_state_changed)

        # Remove default checkbox appearance
        self.setStyleSheet("QCheckBox::indicator { width: 0px; height: 0px; }")

    # Must be a Qt property (not a plain Python property) for QPropertyAnimation
    @pyqtProperty(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def _on_state_changed(self, state):
        """Animate toggle when state changes"""
        self.animation.stop()

        if state == Qt.CheckState.Checked.value:
            # Move circle to right
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(21)  # 44 - 20 - 3 (width - thumb - padding)
        else:
            # Move circle to left
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(3)

        self.animation.start()

    def paintEvent(self, event: QPaintEvent):
        """Custom paint for toggle appearance"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track (background)
        track_rect = QRect(0, 0, self.width(), self.height())
        track_color = QColor(Theme.TOGGLE_ACTIVE) if self.isChecked() else QColor(Theme.TOGGLE_INACTIVE)

        painter.setBrush(track_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(track_rect, 13, 13)

        # Circle (thumb)
        circle_rect = QRect(int(self._circle_position), 3, 20, 20)
        painter.setBrush(QColor(Theme.THUMB))
        painter.drawEllipse(circle_rect)

    def hitButton(self, pos):
        """Override to make entire widget clickable"""
        return self.contentsRect().contains(pos)


class LabeledToggle(QWidget):
    """Toggle switch with label - easier to use"""

    toggled = pyqtSignal(bool)

    def __init__(self, label_text="", parent=None):
        super().__init__(parent)
        self.setup_ui(label_text)

    def setup_ui(self, label_text):
        from PyQt6.QtWidgets import QHBoxLayout, QLabel

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Theme.ITEM_SPACING)

        # Label
        self.label = QLabel(label_text)
        self.label.setStyleSheet(
            Theme.body_text_style()
            + """
            QLabel {
                border: none;
                background: transparent;
            }
        """
        )

        # Toggle
        self.toggle = ToggleSwitch()
        self.toggle.toggled.connect(self.toggled.emit)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.toggle)

    def setChecked(self, checked):
        """Convenience method"""
        self.toggle.setChecked(checked)

    def isChecked(self):
        """Convenience method"""
        return self.toggle.isChecked()

    def setText(self, text):
        """Update label text"""
        self.label.setText(text)
