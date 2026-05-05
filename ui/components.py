from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle


# Dark theme colors
BG_PRIMARY = (0.12, 0.12, 0.12, 1)
BG_SECONDARY = (0.18, 0.18, 0.18, 1)
BG_TERTIARY = (0.22, 0.22, 0.22, 1)

TEXT_PRIMARY = (0.95, 0.95, 0.95, 1)
TEXT_SECONDARY = (0.75, 0.75, 0.75, 1)
TEXT_MUTED = (0.55, 0.55, 0.55, 1)

SURFACE_FILL = (0.18, 0.18, 0.18, 1)
SURFACE_BORDER = (0.3, 0.3, 0.3, 1)

INPUT_FILL = (0.15, 0.15, 0.15, 1)
INPUT_BORDER = (0.25, 0.25, 0.25, 1)

PRIMARY_FILL = (0.85, 0.45, 0.15, 1)
PRIMARY_BORDER = (0.85, 0.45, 0.15, 1)
SUCCESS_FILL = (0.35, 0.65, 0.45, 1)
SUCCESS_BORDER = (0.35, 0.65, 0.45, 1)
DANGER_FILL = (0.75, 0.35, 0.35, 1)
DANGER_BORDER = (0.75, 0.35, 0.35, 1)

CARD_ACTIVE_FILL = (0.2, 0.2, 0.2, 1)
CARD_ACTIVE_BORDER = (0.85, 0.45, 0.15, 1)
CARD_DONE_FILL = (0.18, 0.18, 0.18, 1)
CARD_DONE_BORDER = (0.45, 0.45, 0.45, 1)
CARD_OVERDUE_FILL = (0.18, 0.18, 0.18, 1)
CARD_OVERDUE_BORDER = (0.75, 0.35, 0.35, 1)

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
    """Dark application root."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*BG_PRIMARY)
            self.bg_rect = Rectangle()
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class GlassPane(BoxLayout):
    """Dark panel with border."""
    def __init__(self, fill_color=SURFACE_FILL, border_color=SURFACE_BORDER, shadow_color=None, radius=None, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*fill_color)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        with self.canvas.after:
            Color(*border_color)
            self.border_rect = Rectangle()
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.pos = (self.x, self.y)
        self.border_rect.size = (self.width, 1)


class GlassButton(Button):
    """Dark button."""
    def __init__(self, fill_color=BG_TERTIARY, border_color=None, text_color=TEXT_PRIMARY, shadow_color=None, radius=None, **kwargs):
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(42))
        super().__init__(**kwargs)

        self.fill_color = fill_color
        self.text_color = text_color
        with self.canvas.before:
            Color(*fill_color)
            self.bg_rect = Rectangle()
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def set_palette(self, fill_color=None, border_color=None, text_color=None):
        if fill_color is not None:
            self.fill_color = fill_color
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
            self.fill_color = (0.25, 0.55, 0.35, 1)
        else:
            self.fill_color = SUCCESS_FILL


class IOSSwitch(ToggleButton):
    """Simple toggle button for dark theme."""
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(60), dp(32)))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", BG_TERTIARY)
        kwargs.setdefault("color", TEXT_PRIMARY)
        super().__init__(**kwargs)
        self.active = False


class GlassTextInput(TextInput):
    """Dark text input."""
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

        with self.canvas.after:
            Color(*INPUT_BORDER)
            self.border_rect = Rectangle()
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.border_rect.pos = (self.x, self.y)
        self.border_rect.size = (self.width, 1)


class GlassSpinner(Spinner):
    """Dark spinner."""
    def __init__(self, radius=None, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", INPUT_FILL)
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        super().__init__(**kwargs)

        with self.canvas.after:
            Color(*INPUT_BORDER)
            self.border_rect = Rectangle()
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.border_rect.pos = (self.x, self.y)
        self.border_rect.size = (self.width, 1)


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
    def __init__(self, fill_color=BG_TERTIARY, border_color=None, text_color=TEXT_PRIMARY, radius=None, **kwargs):
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(28))
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)

        self.text_color = text_color
        with self.canvas.before:
            Color(*fill_color)
            self.bg_rect = Rectangle()
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
