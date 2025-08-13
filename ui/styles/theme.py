"""
Professional color system for Mindful Touch
Based on UX designer specifications with accessibility compliance
"""


class Theme:
    # Core color tokens (light theme) - warmer tones
    PRIMARY_600 = "#2F6BA9"
    PRIMARY_500 = "#3B7CBE"
    PRIMARY_100 = "#F0F4F8"
    SUCCESS_600 = "#2E8857"
    WARNING_500 = "#F2A63A"
    ERROR_600 = "#C9483B"

    # Neutral palette - warmer grays
    NEUTRAL_900 = "#1A1818"  # Text primary - warmer black
    NEUTRAL_700 = "#3B3F4A"  # Text secondary/icons - warmer gray
    NEUTRAL_500 = "#8A8E9E"  # Borders - warmer gray
    NEUTRAL_300 = "#C8CDD8"  # Dividers - warmer gray
    NEUTRAL_100 = "#EEEEEE"  # Cards - much more subtle
    CANVAS = "#F2F2F2"  # Window background - much less bright
    WHITE = "#FFFFFF"

    # Focus and interaction
    FOCUS_RING = "rgba(77, 154, 240, 0.4)"

    # Legacy compatibility - map old names to new system
    BACKGROUND = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {CANVAS}, stop:1 {PRIMARY_100})"
    CARD_BACKGROUND = NEUTRAL_100
    CARD_BORDER = NEUTRAL_300
    CARD_SHADOW = "rgba(16, 20, 24, 0.08)"

    # Text colors (updated)
    TEXT_PRIMARY = NEUTRAL_900
    TEXT_SECONDARY = NEUTRAL_700
    TEXT_LIGHT = WHITE
    TEXT_MUTED = NEUTRAL_500

    # Accent colors (updated)
    ACCENT_BLUE = PRIMARY_600
    ACCENT_GREEN = SUCCESS_600
    ACCENT_ORANGE = WARNING_500
    ACCENT_RED = ERROR_600

    # Toggle switch colors (updated)
    TOGGLE_ACTIVE = PRIMARY_500
    TOGGLE_INACTIVE = NEUTRAL_300
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
        """Standard card styling with elevation"""
        return f"""
            QWidget {{
                background-color: {Theme.CARD_BACKGROUND};
                border: 1px solid {Theme.CARD_BORDER};
                border-radius: 12px;
                /* Note: QSS doesn't support box-shadow, handled by container */
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
                background-color: {Theme.PRIMARY_600};
                color: {Theme.WHITE};
                border: none;
                border-radius: 8px;
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                font-weight: 600;
                padding: 12px 24px;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: rgba(47, 110, 169, 0.9);
            }}
            QPushButton:pressed {{
                background-color: rgba(47, 110, 169, 0.8);
            }}
        """

    @staticmethod
    def button_secondary_style():
        """Secondary button styling"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY_600};
                border: 1px solid {Theme.NEUTRAL_500};
                border-radius: 8px;
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                font-weight: 600;
                padding: 12px 24px;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_100};
                border-color: {Theme.PRIMARY_600};
            }}
            QPushButton:pressed {{
                background-color: rgba(232, 241, 250, 0.8);
            }}
            QPushButton:disabled {{
                background-color: transparent;
                color: {Theme.NEUTRAL_500};
                border-color: {Theme.NEUTRAL_300};
            }}
        """

    @staticmethod
    def status_badge_style(status="ready"):
        """Success chip styling - matches designer specs"""
        colors = {"ready": Theme.SUCCESS_600, "detecting": Theme.PRIMARY_600, "alert": Theme.ERROR_600}
        color = colors.get(status, Theme.SUCCESS_600)

        return f"""
            QLabel {{
                background-color: {color};
                color: {Theme.WHITE};
                border: none;
                border-radius: 12px;
                padding: 8px 16px;
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_SMALL}px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """
