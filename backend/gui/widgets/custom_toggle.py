"""Custom toggle switch widget for Mindful Touch."""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush
from PyQt6.QtCore import QTimer


class CustomToggle(QWidget):
    """Custom animated toggle switch widget."""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._knob_position = 3  # Initial position (3px margin)
        
        # Widget properties
        self.setFixedSize(50, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Animation
        self._animation = QPropertyAnimation(self, b"knob_position")
        self._animation.setDuration(300)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Colors
        self._color_off = QColor("#cbd5e0")
        self._color_on = QColor("#667eea")
        self._knob_color = QColor("#ffffff")
        
    @pyqtProperty(int)
    def knob_position(self):
        return self._knob_position
        
    @knob_position.setter
    def knob_position(self, pos):
        self._knob_position = pos
        self.update()
        
    def is_checked(self):
        return self._checked
        
    def set_checked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate_toggle()
            self.toggled.emit(checked)
            
    def _animate_toggle(self):
        """Animate the knob position."""
        start_pos = 3 if not self._checked else 29  # 50 - 18 - 3 = 29
        end_pos = 29 if self._checked else 3
        
        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()
        
    def mousePressEvent(self, event):
        """Handle mouse click to toggle state."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_checked(not self._checked)
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        """Custom paint event to draw the toggle switch."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background track
        track_color = self._color_on if self._checked else self._color_off
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)
        
        # Draw knob
        painter.setBrush(QBrush(self._knob_color))
        
        # Add subtle shadow
        shadow_color = QColor(0, 0, 0, 30)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(self._knob_position + 1, 4, 18, 18)
        
        # Draw main knob
        painter.setBrush(QBrush(self._knob_color))
        painter.drawEllipse(self._knob_position, 3, 18, 18)


class ToggleRow(QWidget):
    """A row containing a toggle switch and label."""
    
    toggled = pyqtSignal(str, bool)
    
    def __init__(self, label_text: str, checked: bool = False, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.setup_ui(checked)
        
    def setup_ui(self, checked: bool):
        """Set up the toggle row UI."""
        from PyQt6.QtWidgets import QHBoxLayout, QLabel
        
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Label
        label = QLabel(self.label_text)
        label.setStyleSheet("""
            QLabel {
                color: #4a5568;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        # Toggle switch
        self.toggle = CustomToggle()
        self.toggle.set_checked(checked)
        self.toggle.toggled.connect(lambda checked: self.toggled.emit(self.label_text, checked))
        
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(self.toggle)
        
        # Hover effect
        self.setStyleSheet("""
            ToggleRow {
                border-radius: 8px;
            }
            ToggleRow:hover {
                background: rgba(102, 126, 234, 0.05);
            }
        """)
        
    def mousePressEvent(self, event):
        """Allow clicking anywhere on the row to toggle."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle.set_checked(not self.toggle.is_checked())
        super().mousePressEvent(event)
        
    def is_checked(self):
        """Get the current toggle state."""
        return self.toggle.is_checked()
        
    def set_checked(self, checked: bool):
        """Set the toggle state."""
        self.toggle.set_checked(checked)