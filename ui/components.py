from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget


TEXT_PRIMARY = (0.1, 0.11, 0.14, 1)
TEXT_SECONDARY = (0.35, 0.39, 0.46, 1)
TEXT_MUTED = (0.54, 0.57, 0.63, 1)

SURFACE_FILL = (1, 1, 1, 0.98)
SURFACE_FILL_ALT = (0.96, 0.97, 0.99, 0.99)
SURFACE_BORDER = (0.85, 0.87, 0.91, 1)
SURFACE_SHADOW = (0.49, 0.55, 0.66, 0.12)

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
    Clock.schedule_once(update_text_size, 0)
    return label


def bind_auto_height(label, min_height=dp(24), extra=dp(6)):
    """Resize a label height based on rendered text."""

    def update_height(*_):
        label.height = max(min_height, label.texture_size[1] + extra)

    label.bind(texture_size=update_height, text=update_height)
    Clock.schedule_once(update_height, 0)
    return label


class GlassRoot(BoxLayout):
    """Application root with a dark layered background."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg_color = Color(0.04, 0.06, 0.1, 1)
            self._bg_rect = Rectangle()

            self._blob_one_color = Color(0.37, 0.67, 0.97, 0.18)
            self._blob_one = Ellipse()

            self._blob_two_color = Color(0.97, 0.73, 0.37, 0.15)
            self._blob_two = Ellipse()

            self._blob_three_color = Color(0.92, 0.53, 0.67, 0.12)
            self._blob_three = Ellipse()

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *_):
        self._bg_color.rgba = (0.95, 0.96, 0.98, 1)
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        self._blob_one.pos = (self.x - dp(60), self.top - dp(240))
        self._blob_one.size = (dp(260), dp(260))

        self._blob_two.pos = (self.right - dp(220), self.y + dp(120))
        self._blob_two.size = (dp(220), dp(220))

        self._blob_three.pos = (self.center_x - dp(90), self.center_y - dp(320))
        self._blob_three.size = (dp(180), dp(180))


class GlassPane(BoxLayout):
    """Rounded panel with subtle border and shadow."""

    def __init__(
        self,
        fill_color=SURFACE_FILL,
        border_color=SURFACE_BORDER,
        shadow_color=SURFACE_SHADOW,
        radius=dp(28),
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.fill_color = fill_color
        self.border_color = border_color
        self.shadow_color = shadow_color
        self.radius = radius

        with self.canvas.before:
            self._shadow_color = Color(*self.shadow_color)
            self._shadow_rect = RoundedRectangle(radius=[self.radius])

            self._fill_color = Color(*self.fill_color)
            self._fill_rect = RoundedRectangle(radius=[self.radius])

        with self.canvas.after:
            self._border_color = Color(*self.border_color)
            self._border_line = Line(width=0.85)

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def set_palette(self, fill_color=None, border_color=None):
        if fill_color is not None:
            self.fill_color = fill_color
        if border_color is not None:
            self.border_color = border_color
        self._update_canvas()

    def _update_canvas(self, *_):
        self._shadow_color.rgba = self.shadow_color
        self._shadow_rect.pos = (self.x, self.y - dp(5))
        self._shadow_rect.size = self.size
        self._shadow_rect.radius = [self.radius]

        self._fill_color.rgba = self.fill_color
        self._fill_rect.pos = self.pos
        self._fill_rect.size = self.size
        self._fill_rect.radius = [self.radius]

        self._border_color.rgba = self.border_color
        self._border_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.radius,
        )


class GlassButton(Button):
    """Rounded dark button with readable text."""

    def __init__(
        self,
        fill_color=SURFACE_FILL_ALT,
        border_color=SURFACE_BORDER,
        text_color=TEXT_PRIMARY,
        shadow_color=SURFACE_SHADOW,
        radius=dp(24),
        **kwargs,
    ):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(42))
        super().__init__(**kwargs)

        self.fill_color = fill_color
        self.border_color = border_color
        self.shadow_color = shadow_color
        self.text_color = text_color
        self.radius = radius

        with self.canvas.before:
            self._shadow_color = Color(*self.shadow_color)
            self._shadow_rect = RoundedRectangle(radius=[self.radius])

            self._fill_color = Color(*self.fill_color)
            self._fill_rect = RoundedRectangle(radius=[self.radius])

        with self.canvas.after:
            self._border_color = Color(*self.border_color)
            self._border_line = Line(width=0.8)

        self.bind(pos=self._update_canvas, size=self._update_canvas, state=self._update_state)
        Clock.schedule_once(self._update_canvas, 0)

    def set_palette(self, fill_color=None, border_color=None, text_color=None):
        if fill_color is not None:
            self.fill_color = fill_color
        if border_color is not None:
            self.border_color = border_color
        if text_color is not None:
            self.text_color = text_color
            self.color = text_color
        self._update_canvas()

    def _update_state(self, *_):
        if self.state == "down":
            pressed = tuple(max(channel - 0.08, 0) for channel in self.fill_color[:3]) + (
                self.fill_color[3],
            )
            self._fill_color.rgba = pressed
        else:
            self._fill_color.rgba = self.fill_color

    def _update_canvas(self, *_):
        self.color = self.text_color
        self._shadow_color.rgba = self.shadow_color
        self._shadow_rect.pos = (self.x, self.y - dp(4))
        self._shadow_rect.size = self.size
        self._shadow_rect.radius = [self.radius]

        self._fill_color.rgba = self.fill_color
        self._fill_rect.pos = self.pos
        self._fill_rect.size = self.size
        self._fill_rect.radius = [self.radius]

        self._border_color.rgba = self.border_color
        self._border_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.radius,
        )


class PrimaryGlassButton(GlassButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", PRIMARY_FILL)
        kwargs.setdefault("border_color", PRIMARY_BORDER)
        kwargs.setdefault("text_color", (1, 1, 1, 1))
        super().__init__(**kwargs)


class SuccessGlassButton(GlassButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", SUCCESS_FILL)
        kwargs.setdefault("border_color", SUCCESS_BORDER)
        kwargs.setdefault("text_color", (1, 1, 1, 1))
        super().__init__(**kwargs)


class DangerGlassButton(GlassButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", DANGER_FILL)
        kwargs.setdefault("border_color", DANGER_BORDER)
        kwargs.setdefault("text_color", (1, 1, 1, 1))
        super().__init__(**kwargs)


class CheckIconButton(SuccessGlassButton):
    """Circular success button with a drawn checkmark."""

    def __init__(self, **kwargs):
        kwargs.setdefault("text", "")
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(28))
        kwargs.setdefault("height", dp(28))
        kwargs.setdefault("radius", dp(14))
        super().__init__(**kwargs)

        with self.canvas.after:
            self._icon_color = Color(1, 1, 1, 1)
            self._icon_line = Line(width=1.2, cap="round", joint="round")

        self.bind(pos=self._update_icon, size=self._update_icon)
        Clock.schedule_once(self._update_icon, 0)

    def _update_icon(self, *_):
        left = self.x + self.width * 0.34
        mid_x = self.x + self.width * 0.47
        right = self.x + self.width * 0.64
        low = self.y + self.height * 0.48
        mid_y = self.y + self.height * 0.36
        high = self.y + self.height * 0.58
        self._icon_line.points = [left, low, mid_x, mid_y, right, high]

    def set_selected(self, selected):
        if selected:
            self.set_palette(
                fill_color=(0.25, 0.65, 0.43, 1),
                border_color=(0.25, 0.65, 0.43, 1),
                text_color=(1, 1, 1, 1),
            )
        else:
            self.set_palette(
                fill_color=SUCCESS_FILL,
                border_color=SUCCESS_BORDER,
                text_color=(1, 1, 1, 1),
            )


class IOSSwitch(ButtonBehavior, Widget):
    """Custom iOS-like toggle with app palette."""

    active = BooleanProperty(False)
    active_color = ListProperty([0.31, 0.75, 0.42, 1])
    inactive_color = ListProperty([0.84, 0.87, 0.92, 1])
    thumb_color = ListProperty([1, 1, 1, 1])
    border_color = ListProperty([0.8, 0.83, 0.89, 1])

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(54), dp(32)))
        super().__init__(**kwargs)
        with self.canvas.before:
            self._track_color = Color()
            self._track = RoundedRectangle()
        with self.canvas.after:
            self._border_color = Color()
            self._border = Line(width=0.9)
            self._thumb_shadow_color = Color(0, 0, 0, 0.1)
            self._thumb_shadow = Ellipse()
            self._thumb_color = Color()
            self._thumb = Ellipse()

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            active=self._update_canvas,
            disabled=self._update_canvas,
        )
        Clock.schedule_once(self._update_canvas, 0)

    def on_press(self):
        if not self.disabled:
            self.active = not self.active

    def _update_canvas(self, *_):
        radius = self.height / 2
        track_color = self.active_color if self.active else self.inactive_color
        if self.disabled:
            track_color = [track_color[0], track_color[1], track_color[2], 0.45]

        self._track_color.rgba = track_color
        self._track.pos = self.pos
        self._track.size = self.size
        self._track.radius = [radius]

        self._border_color.rgba = self.border_color if not self.active else self.active_color
        self._border.rounded_rectangle = (self.x, self.y, self.width, self.height, radius)

        thumb_size = max(self.height - dp(4), dp(18))
        thumb_y = self.y + (self.height - thumb_size) / 2
        thumb_x = self.right - thumb_size - dp(2) if self.active else self.x + dp(2)

        self._thumb_shadow.pos = (thumb_x, thumb_y - dp(1))
        self._thumb_shadow.size = (thumb_size, thumb_size)
        self._thumb_color.rgba = self.thumb_color if not self.disabled else [1, 1, 1, 0.8]
        self._thumb.pos = (thumb_x, thumb_y)
        self._thumb.size = (thumb_size, thumb_size)


class GlassTextInput(TextInput):
    """Dark input field with rounded border."""

    def __init__(self, radius=dp(22), **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("foreground_color", TEXT_PRIMARY)
        kwargs.setdefault("cursor_color", (0.2, 0.54, 0.95, 1))
        kwargs.setdefault("cursor_width", dp(2.2))
        kwargs.setdefault("hint_text_color", TEXT_MUTED)
        kwargs.setdefault("selection_color", (0.34, 0.56, 0.98, 0.35))
        kwargs.setdefault("padding", [dp(14), dp(12), dp(14), dp(12)])
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        kwargs.setdefault("font_size", FONT_SIZE)
        super().__init__(**kwargs)

        self.radius = radius
        self.cursor_blink = False
        self._caret_visible = False
        self._caret_event = None

        with self.canvas.before:
            self._fill_color = Color(*INPUT_FILL)
            self._fill_rect = RoundedRectangle(radius=[self.radius])
        with self.canvas.after:
            self._border_color = Color(*INPUT_BORDER)
            self._border_line = Line(width=0.8)
            self._caret_color = Color(0.2, 0.54, 0.95, 0)
            self._caret_rect = Rectangle(size=(0, 0))

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            focus=self._on_focus_change,
            cursor_pos=self._refresh_caret,
            cursor=self._show_caret_now,
            text=self._show_caret_now,
        )
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *_):
        self._fill_rect.pos = self.pos
        self._fill_rect.size = self.size
        self._fill_rect.radius = [self.radius]
        self._border_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.radius,
        )
        self._refresh_caret()

    def _draw_line(self, *args, **kwargs):
        if self.text:
            color = self.foreground_color
        else:
            color = self.hint_text_color
        self.canvas.add(Color(*color, group="text_tint"))
        return super()._draw_line(*args, **kwargs)

    def _on_focus_change(self, *_):
        if self.focus:
            self._show_caret_now()
            if self._caret_event is None:
                self._caret_event = Clock.schedule_interval(self._toggle_caret, 0.55)
        else:
            if self._caret_event is not None:
                self._caret_event.cancel()
                self._caret_event = None
            self._caret_visible = False
            self._refresh_caret()

    def _toggle_caret(self, *_):
        if not self.focus:
            self._caret_visible = False
            self._refresh_caret()
            return False
        self._caret_visible = not self._caret_visible
        self._refresh_caret()
        return True

    def _show_caret_now(self, *_):
        if self.focus:
            self._caret_visible = True
            self._refresh_caret()

    def _refresh_caret(self, *_):
        if not self.focus or not self._caret_visible:
            self._caret_color.rgba = (self.cursor_color[0], self.cursor_color[1], self.cursor_color[2], 0)
            self._caret_rect.size = (0, 0)
            return

        inner_height = max(self.height - self.padding[1] - self.padding[3], dp(16))
        effective_line_height = self.line_height if self.line_height > 2 else self.font_size * 1.15
        caret_height = min(inner_height, max(effective_line_height, self.font_size * 1.0))

        cursor_x, cursor_top = self.cursor_pos
        caret_x = min(max(cursor_x, self.x + self.padding[0]), self.right - self.padding[2] - self.cursor_width)
        caret_y = cursor_top - caret_height

        self._caret_color.rgba = self.cursor_color
        self._caret_rect.pos = (caret_x, caret_y)
        self._caret_rect.size = (self.cursor_width, caret_height)


class DarkSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", INPUT_FILL)
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_size", "14sp")
        super().__init__(**kwargs)


class GlassSpinner(Spinner):
    """Dark spinner styled like an input field."""

    def __init__(self, radius=dp(22), **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        kwargs.setdefault("option_cls", DarkSpinnerOption)
        super().__init__(**kwargs)

        self.radius = radius
        with self.canvas.before:
            self._fill_color = Color(*INPUT_FILL)
            self._fill_rect = RoundedRectangle(radius=[self.radius])
        with self.canvas.after:
            self._border_color = Color(*INPUT_BORDER)
            self._border_line = Line(width=0.8)

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *_):
        self._fill_rect.pos = self.pos
        self._fill_rect.size = self.size
        self._fill_rect.radius = [self.radius]
        self._border_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.radius,
        )


class SectionTitle(Label):
    """Readable section heading."""

    def __init__(self, **kwargs):
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(34))
        kwargs.setdefault("halign", "left")
        kwargs.setdefault("valign", "middle")
        super().__init__(**kwargs)
        self.bind(size=self._sync_text_box)
        Clock.schedule_once(self._sync_text_box, 0)

    def _sync_text_box(self, *_):
        self.text_size = (max(self.width, dp(10)), self.height)


class BadgeLabel(Label):
    """Small rounded badge for statuses and categories."""

    def __init__(
        self,
        fill_color=(0.17, 0.23, 0.36, 1),
        border_color=(0.34, 0.48, 0.74, 0.95),
        text_color=(1, 1, 1, 1),
        radius=dp(16),
        **kwargs,
    ):
        kwargs.setdefault("color", text_color)
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(28))
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)

        self.fill_color = fill_color
        self.border_color = border_color
        self.text_color = text_color
        self.radius = radius

        with self.canvas.before:
            self._fill_color = Color(*self.fill_color)
            self._fill_rect = RoundedRectangle(radius=[self.radius])
        with self.canvas.after:
            self._border_color = Color(*self.border_color)
            self._border_line = Line(width=0.78)

        self.bind(
            pos=self._update_canvas,
            size=self._update_canvas,
            texture_size=self._update_size,
            text=self._update_size,
        )
        Clock.schedule_once(self._update_size, 0)

    def _update_size(self, *_):
        self.width = max(dp(80), self.texture_size[0] + dp(24))
        self._update_canvas()

    def _update_canvas(self, *_):
        self.color = self.text_color
        self._fill_rect.pos = self.pos
        self._fill_rect.size = self.size
        self._fill_rect.radius = [self.radius]
        self._border_line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            self.radius,
        )
