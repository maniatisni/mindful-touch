"""
Mindful Touch design system
Calm, warm, minimal — dusty blue / sage / clay on warm cream
"""

# Logo mark: two strokes on a 48x48 grid (cup in dusty blue, heart in clay)
LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <path d="M8 27 C8 35 15 41 24 41 C33 41 40 35 40 27" fill="none" stroke="#5C7C99" stroke-width="5" stroke-linecap="round"/>
  <path d="M24 22 C24 22 14 15 14 9 A5 5 0 0 1 24 9 A5 5 0 0 1 34 9 C34 15 24 22 24 22 Z" fill="none" stroke="#B67F5C" stroke-width="4"/>
</svg>"""


class Theme:
    # Core color tokens
    CANVAS = "#F7F3EC"  # App window background
    SURFACE = "#FFFFFF"  # Cards, panels
    INK = "#2B2926"  # Primary text
    INK_SOFT = "#6B655D"  # Secondary/body text
    MUTED = "#A2957F"  # Small caps labels, captions
    BORDER = "#E4DCCE"  # Card borders, dividers
    HAIRLINE = "#F0EAE0"  # Row separators inside cards

    PRIMARY = "#5C7C99"  # Dusty blue — buttons, links, active toggle
    PRIMARY_HOVER = "#4C6C89"
    SAGE = "#7C9473"  # Success / ready / mindful stops
    SAGE_HOVER = "#688061"
    CLAY = "#B67F5C"  # Touch noticed / alert accents
    CLAY_BORDER = "#E6D9CC"  # Outlined clay button border

    SOFT_BLUE = "#E7EDF1"  # Detecting pill background
    SOFT_SAGE = "#EEF2EA"  # Ready pill background
    SOFT_CLAY = "#F3E8DE"  # Touch noticed pill background

    TOGGLE_OFF = "#D8CFBE"  # Inactive toggle track
    THUMB = "#FFF9F4"  # Toggle thumb / cream text on primary
    FEED_BG = "#EFEAE2"  # Camera placeholder background

    WHITE = "#FFFFFF"

    # Legacy aliases (kept so existing widget code keeps working)
    BACKGROUND = CANVAS
    CARD_BACKGROUND = SURFACE
    CARD_BORDER = BORDER
    TEXT_PRIMARY = INK
    TEXT_SECONDARY = INK_SOFT
    TEXT_MUTED = MUTED
    PRIMARY_600 = PRIMARY
    PRIMARY_500 = PRIMARY_HOVER
    PRIMARY_100 = SOFT_BLUE
    SUCCESS_600 = SAGE
    ERROR_600 = CLAY
    WARNING_500 = CLAY
    NEUTRAL_300 = BORDER
    NEUTRAL_500 = MUTED
    TOGGLE_ACTIVE = PRIMARY
    TOGGLE_INACTIVE = TOGGLE_OFF

    # Spacing & shape
    CARD_MARGIN = 24
    CARD_PADDING = 24
    ITEM_SPACING = 14
    SECTION_SPACING = 24
    BORDER_RADIUS = 16

    # Window settings (design frame is 1040x700)
    WINDOW_MIN_WIDTH = 1040
    WINDOW_MIN_HEIGHT = 700

    # Fonts — Work Sans is bundled and loaded at startup
    FONT_TITLE = "Work Sans"
    FONT_BODY = "Work Sans"
    FONT_SIZE_TITLE = 18
    FONT_SIZE_SECTION = 13
    FONT_SIZE_BODY = 15
    FONT_SIZE_SMALL = 12

    @staticmethod
    def card_style():
        """Standard surface card"""
        return f"""
            QWidget {{
                background-color: {Theme.SURFACE};
                border: 1px solid {Theme.BORDER};
                border-radius: {Theme.BORDER_RADIUS}px;
            }}
        """

    @staticmethod
    def section_title_style():
        """Small section label inside cards"""
        return f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_SECTION}px;
                font-weight: 600;
                color: {Theme.INK_SOFT};
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def helper_text_style():
        """Muted helper line under a section label"""
        return f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: 13px;
                color: {Theme.MUTED};
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def body_text_style():
        """Body text"""
        return f"""
            QLabel {{
                font-family: {Theme.FONT_BODY};
                font-size: {Theme.FONT_SIZE_BODY}px;
                color: {Theme.INK};
                border: none;
                background: transparent;
            }}
        """

    @staticmethod
    def button_primary_style():
        """Primary pill button (dusty blue, cream text)"""
        return f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.THUMB};
                border: none;
                border-radius: 22px;
                font-family: {Theme.FONT_BODY};
                font-size: 14px;
                font-weight: 600;
                padding: 12px 28px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {Theme.TOGGLE_OFF};
                color: {Theme.SURFACE};
            }}
        """

    @staticmethod
    def button_secondary_style():
        """Quiet outlined pill button"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.INK_SOFT};
                border: 1px solid {Theme.BORDER};
                border-radius: 22px;
                font-family: {Theme.FONT_BODY};
                font-size: 14px;
                font-weight: 600;
                padding: 12px 28px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SOFT_BLUE};
                border-color: {Theme.PRIMARY};
                color: {Theme.PRIMARY};
            }}
            QPushButton:disabled {{
                color: {Theme.TOGGLE_OFF};
                border-color: {Theme.HAIRLINE};
            }}
        """

    @staticmethod
    def button_pause_style():
        """Outlined clay pill button — pause detection"""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.CLAY};
                border: 1px solid {Theme.CLAY_BORDER};
                border-radius: 22px;
                font-family: {Theme.FONT_BODY};
                font-size: 14px;
                font-weight: 600;
                padding: 12px 28px;
                min-height: 20px;
            }}
            QPushButton:hover {{
                background-color: {Theme.SOFT_CLAY};
                border-color: {Theme.CLAY};
            }}
            QPushButton:disabled {{
                color: {Theme.TOGGLE_OFF};
                border-color: {Theme.HAIRLINE};
            }}
        """

    @staticmethod
    def status_badge_style(status="ready"):
        """Soft status pill: colored text on a pale tinted background"""
        colors = {
            "ready": (Theme.SOFT_SAGE, Theme.SAGE),
            "detecting": (Theme.SOFT_BLUE, Theme.PRIMARY),
            "alert": (Theme.SOFT_CLAY, Theme.CLAY),
            "error": (Theme.SOFT_CLAY, Theme.CLAY),
        }
        bg, fg = colors.get(status, (Theme.SOFT_SAGE, Theme.SAGE))

        return f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: none;
                border-radius: 14px;
                padding: 6px 16px;
                font-family: {Theme.FONT_BODY};
                font-size: 12px;
                font-weight: 600;
            }}
        """
