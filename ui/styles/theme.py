"""
Glass-like transparent theme for Mindful Touch
Modern, minimal design with generous spacing
"""


class Theme:
    # Colors - Glass theme with transparency
    BACKGROUND = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(240, 248, 255, 0.15), stop:1 rgba(220, 240, 255, 0.2))"

    # Card colors - Glass effect
    CARD_BACKGROUND = "rgba(255, 255, 255, 0.12)"
    CARD_BORDER = "rgba(255, 255, 255, 0.2)"
    CARD_SHADOW = "rgba(0, 0, 0, 0.05)"

    # Text colors
    TEXT_PRIMARY = "#1A202C"  # Very dark gray (better contrast)
    TEXT_SECONDARY = "#4A5568"  # Dark gray
    TEXT_LIGHT = "#FFFFFF"  # White for dark backgrounds
    TEXT_MUTED = "#718096"  # Medium gray

    # Accent colors
    ACCENT_BLUE = "#3498DB"  # Primary blue
    ACCENT_GREEN = "#2ECC71"  # Success green
    ACCENT_ORANGE = "#FF9800"  # Warning orange
    ACCENT_RED = "#E74C3C"  # Alert red

    # Toggle switch colors
    TOGGLE_ACTIVE = "#4CAF50"  # Active green
    TOGGLE_INACTIVE = "#BDC3C7"  # Inactive gray
    TOGGLE_BACKGROUND = "rgba(255, 255, 255, 0.2)"

    # Spacing constants
    CARD_MARGIN = 20
    CARD_PADDING = 24
    ITEM_SPACING = 16
    SECTION_SPACING = 32
    BORDER_RADIUS = 16

    # Window settings
    WINDOW_MIN_WIDTH = 1400
    WINDOW_MIN_HEIGHT = 900

    # Fonts
    FONT_TITLE = "SF Pro Display, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    FONT_BODY = "SF Pro Text, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    FONT_SIZE_TITLE = 28
    FONT_SIZE_SECTION = 18
    FONT_SIZE_BODY = 14
    FONT_SIZE_SMALL = 12

    @staticmethod
    def card_style():
        """Standard card styling"""
        return f"""
            QWidget {{
                background-color: {Theme.CARD_BACKGROUND};
                border: none;
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """

    @staticmethod
    def section_title_style():
        """Section title styling"""
        return f"""
            QLabel {{
                font-family: {Theme.FONT_TITLE};
                font-size: {Theme.FONT_SIZE_SECTION}px;
                font-weight: 600;
                color: {Theme.TEXT_PRIMARY};
                margin-bottom: {Theme.ITEM_SPACING // 2}px;
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def body_text_style():
        """Body text styling"""
        return f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                color: {Theme.TEXT_SECONDARY};
                line-height: 1.4;
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def button_primary_style():
        """Primary button styling"""
        return f"""
            QPushButton {{
                background-color: {Theme.ACCENT_BLUE};
                color: {Theme.TEXT_LIGHT};
                border: none;
                border-radius: 12px;
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                font-weight: 600;
                padding: 12px 24px;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: rgba(52, 152, 219, 0.9);
            }}
            QPushButton:pressed {{
                background-color: rgba(52, 152, 219, 0.8);
            }}
        """

    @staticmethod
    def status_badge_style(status="ready"):
        """Status badge styling"""
        colors = {"ready": Theme.ACCENT_GREEN, "detecting": Theme.ACCENT_BLUE, "alert": Theme.ACCENT_RED}
        color = colors.get(status, Theme.ACCENT_GREEN)

        return f"""
            QLabel {{
                background-color: {color};
                color: {Theme.TEXT_LIGHT};
                border: none;
                border-radius: 16px;
                padding: 8px 16px;
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_SMALL}px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """
