from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget


TEXT_PRIMARY = (0.1, 0.11, 0.14, 1)
TEXT_SECONDARY = (0.35, 0.39, 0.46, 1)
TEXT_MUTED = (0.54, 0.57, 0.63, 1)

SURFACE_FILL = (1, 1, 1, 1)
SURFACE_FILL_ALT = (0.96, 0.97, 0.99, 1)
SURFACE_BORDER = (0.85, 0.87, 0.91, 1)

INPUT_FILL = (0.96, 0.97, 0.99, 1)
INPUT_BORDER = (0.84, 0.87, 0.92, 1)

PRIMARY_FILL = (0.33, 0.66, 0.95, 1)
PRIMARY_BORDER = (0.33, 0.66, 0.95, 1)
SUCCESS_FILL = (0.34, 0.75, 0.52, 1)
SUCCESS_BORDER = (0.34, 0.75, 0.52, 1)
DANGER_FILL = (0.94, 0.47, 0.5, 1)
DANGER_BORDER = (0.94, 0.47, 0.5, 1)

CARD_ACTIVE_FILL = (0.35, 0.66, 0.95, 1)
CARD_ACTIVE_BORDER = (0.35, 0.66, 0.95, 1)
CARD_DONE_FILL = (0.63, 0.67, 0.71, 1)
CARD_DONE_BORDER = (0.63, 0.67, 0.71, 1)
CARD_OVERDUE_FILL = (0.94, 0.55, 0.58, 1)
CARD_OVERDUE_BORDER = (0.94, 0.55, 0.58, 1)

FONT_SIZE = "14sp"


def bind_text_size(label, horizontal_padding=0):
    """Bind label width to text wrapping width."""
    def update_text_size(*_):
        width = max(label.width - horizontal_padding, dp(10))
        label.text_size = (width, None)
    label.bind(width=update_text_size)
    update_text_size()
    return label


def bind_auto_height(label, min_height=dp(24), extra=dp(6)):
    """Resize a label height based on rendered text."""
    def update_height(*_):
        label.height = max(min_height, label.texture_size[1] + extra)
    label.bind(texture_size=update_height, text=update_height)
    update_height()
    return label


class GlassRoot(BoxLayout):
    """Application root."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class GlassPane(BoxLayout):
    """Simple panel."""
    def __init__(self, fill_color=SURFACE_FILL, border_color=None, shadow_color=None, radius=None, **kwargs):
        super().__init__(**kwargs)


class GlassButton(Button):
    """Simple button with basic colors."""
    def __init__(self, fill_color=SURFACE_FILL_ALT, border_color=None, text_color=TEXT_PRIMARY, shadow_color=None, radius=None, **kwargs):
        kwargs.setdefault("background_color", fill_color)
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(42))
        super().__init__(**kwargs)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text_color = text_color

    def set_palette(self, fill_color=None, border_color=None, text_color=None):
        if fill_color is not None:
            self.background_color = fill_color
        if text_color is not None:
            self.color = text_color


class PrimaryGlassButton(GlassButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", PRIMARY_FILL)
        kwargs.setdefault("text_color", (1, 1, 1, 1))
        super().__init__(**kwargs)


class SuccessGlassButton(GlassButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", SUCCESS_FILL)
        kwargs.setdefault("text_color", (1, 1, 1, 1))
        super().__init__(**kwargs)


class DangerGlassButton(GlassButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", DANGER_FILL)
        kwargs.setdefault("text_color", (1, 1, 1, 1))
        super().__init__(**kwargs)


class CheckIconButton(SuccessGlassButton):
    """Simple circular button for marking tasks done."""
    def __init__(self, **kwargs):
        kwargs.setdefault("text", "✓")
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(42))
        kwargs.setdefault("height", dp(42))
        super().__init__(**kwargs)

    def set_selected(self, selected):
        if selected:
            self.background_color = (0.25, 0.65, 0.43, 1)
        else:
            self.background_color = SUCCESS_FILL


class IOSSwitch(ToggleButton):
    """Simple toggle button instead of custom switch."""
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(60), dp(32)))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        super().__init__(**kwargs)
        self.active = False


class GlassTextInput(TextInput):
    """Simple text input."""
    def __init__(self, radius=None, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("background_color", INPUT_FILL)
        kwargs.setdefault("foreground_color", TEXT_PRIMARY)
        kwargs.setdefault("hint_text_color", TEXT_MUTED)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        kwargs.setdefault("font_size", FONT_SIZE)
        super().__init__(**kwargs)


class GlassSpinner(Spinner):
    """Simple spinner."""
    def __init__(self, radius=None, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", INPUT_FILL)
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        super().__init__(**kwargs)


class SectionTitle(Label):
    """Section heading."""
    def __init__(self, **kwargs):
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(34))
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)


class BadgeLabel(Label):
    """Badge for status/category."""
    def __init__(self, fill_color=(0.17, 0.23, 0.36, 1), border_color=None, text_color=(1, 1, 1, 1), radius=None, **kwargs):
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(28))
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)
        self.text_color = text_color
