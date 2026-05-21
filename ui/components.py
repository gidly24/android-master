from pathlib import Path

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput

_ROBOTO_BOLD_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Roboto-Bold.ttf"
FONT_NAME = str(_ROBOTO_BOLD_PATH) if _ROBOTO_BOLD_PATH.exists() else "Roboto"
FONT_SIZE = "16sp"
APP_BACKGROUND = (0.1333333333, 0.1411764706, 0.1647058824, 1)  # #22242A
POPUP_SURFACE = (0.1529411765, 0.1607843137, 0.1882352941, 1)  # #272930
INPUT_FILL = (0.2117647059, 0.2196078431, 0.2509803922, 1)  # #363840
TEXT_PRIMARY = (0.8392156863, 0.8470588235, 0.8784313725, 1)  # #D6D8E0
TEXT_SECONDARY = TEXT_PRIMARY
TEXT_MUTED = TEXT_PRIMARY
M3_PRIMARY = (0.0509803922, 0.3960784314, 0.8509803922, 1)  # #0D65D9
M3_SURFACE = APP_BACKGROUND
M3_SURFACE_VARIANT = POPUP_SURFACE
M3_OUTLINE = INPUT_FILL
SPINNER_FILL = INPUT_FILL
TRANSPARENT_APP = (APP_BACKGROUND[0], APP_BACKGROUND[1], APP_BACKGROUND[2], 0)

CARD_ACTIVE_FILL = POPUP_SURFACE
CARD_ACTIVE_BORDER = POPUP_SURFACE
CARD_DONE_FILL = POPUP_SURFACE
CARD_DONE_BORDER = POPUP_SURFACE
CARD_OVERDUE_FILL = POPUP_SURFACE
CARD_OVERDUE_BORDER = POPUP_SURFACE


def _capsule_radius(size, fallback_radius=None):
    max_radius = max(min(size[0], size[1]) / 2, 0)
    if fallback_radius is None:
        return max_radius
    return min(fallback_radius, max_radius)


def bind_text_size(label, horizontal_padding=0):
    def update_text_size(*_):
        width = max(label.width - horizontal_padding, dp(10))
        label.text_size = (width, None)

    label.bind(width=update_text_size)
    Clock.schedule_once(update_text_size, 0)
    return label


def bind_auto_height(label, min_height=dp(24), extra=dp(6)):
    def update_height(*_):
        label.height = max(min_height, label.texture_size[1] + extra)

    label.bind(texture_size=update_height, text=update_height)
    Clock.schedule_once(update_height, 0)
    return label


class MaterialRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._bg = Color(*APP_BACKGROUND)
            self._rect = Rectangle()
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


class MaterialCard(BoxLayout):
    def __init__(self, fill_color=M3_SURFACE, border_color=M3_OUTLINE, radius=dp(24), **kwargs):
        super().__init__(**kwargs)
        self.fill_color = fill_color
        self.border_color = border_color
        self.radius = radius
        with self.canvas.before:
            self._fill = Color(*self.fill_color)
            self._rect = RoundedRectangle(radius=[0])
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def set_palette(self, fill_color=None, border_color=None):
        if fill_color is not None:
            self.fill_color = fill_color
        if border_color is not None:
            self.border_color = border_color
        self._update_canvas()

    def _update_canvas(self, *_):
        self._fill.rgba = self.fill_color
        self._rect.pos = self.pos
        self._rect.size = self.size
        r = _capsule_radius(self.size, self.radius)
        self._rect.radius = [r, r, r, r]


class MaterialButton(Button):
    def __init__(
            self,
            fill_color=M3_PRIMARY,
            border_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            radius=None,
            **kwargs,
    ):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", TRANSPARENT_APP)
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(42))
        kwargs.setdefault("bold", True)
        kwargs.setdefault("color", text_color)
        super().__init__(**kwargs)
        self.fill_color = fill_color
        self.border_color = border_color
        self.text_color = text_color
        self.radius = radius
        with self.canvas.before:
            self._fill = Color(*self.fill_color)
            self._rect = RoundedRectangle(radius=[0])
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
            self._fill.rgba = POPUP_SURFACE
        else:
            self._fill.rgba = self.fill_color

    def _update_canvas(self, *_):
        self._update_state()
        self.color = self.text_color
        self._rect.pos = self.pos
        self._rect.size = self.size
        r = _capsule_radius(self.size, self.radius)
        self._rect.radius = [r, r, r, r]


class FilledButton(MaterialButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", M3_PRIMARY)
        kwargs.setdefault("border_color", M3_PRIMARY)
        kwargs.setdefault("text_color", TEXT_PRIMARY)
        super().__init__(**kwargs)


class DangerButton(MaterialButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("fill_color", M3_PRIMARY)
        kwargs.setdefault("border_color", M3_PRIMARY)
        kwargs.setdefault("text_color", TEXT_PRIMARY)
        super().__init__(**kwargs)


class MaterialTextInput(TextInput):
    def __init__(self, radius=dp(24), **kwargs):
        # 1. Возвращаем стандартные фоновые свойства Kivy в пустые строки,
        # чтобы дефолтная белая коробка Windows не рисовалась поверх нашей плашки
        # 1. Возвращаем стандартные фоновые свойства Kivy в пустые строки,
        # чтобы дефолтная белая коробка Windows не рисовалась поверх нашей плашки
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("background_disabled_normal", "")  # <-- ИСПРАВЛЕНО НА ВАЛИДНОЕ СВОЙСТВО

        # 2. Важно: оставляем цвет TRANSPARENT_APP, чтобы Kivy не рисовал свой фон,
        # но мы полностью перепишем холст before
        kwargs.setdefault("background_color", TRANSPARENT_APP)

        kwargs.setdefault("foreground_color", TEXT_PRIMARY)
        kwargs.setdefault("disabled_foreground_color", TEXT_PRIMARY)
        kwargs.setdefault("cursor_color", M3_PRIMARY)
        kwargs.setdefault("selection_color", (M3_PRIMARY[0], M3_PRIMARY[1], M3_PRIMARY[2], 0.35))
        kwargs.setdefault("cursor_width", dp(2))
        kwargs.setdefault("cursor_blink", True)
        kwargs.setdefault("hint_text_color", TEXT_MUTED)
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("padding", [dp(12), dp(12), dp(12), dp(12)])
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("input_type", "text")
        kwargs.setdefault("keyboard_suggestions", True)

        super().__init__(**kwargs)
        self.radius = radius

        # 3. Магия слоев: canvas.before выполняется строго ДО отрисовки текста.
        # Чтобы текст и каретка не перекрывались нашей плашкой, мы изолируем
        # контекст цвета подложки, а в самом конце СБРАСЫВАЕМ цвет в чисто белый (1,1,1,1).
        # Kivy использует белый цвет как базовый множитель для вывода текста и каретки!
        with self.canvas.before:
            self._fill = Color(*INPUT_FILL)
            self._rect = RoundedRectangle(radius=[0])
            self._ctx_reset = Color(1, 1, 1, 1)  # Этот сброс вернет текст на передний план

        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

        # Наше скругление для всех 4 углов (исправление для Android)
        r = _capsule_radius(self.size, self.radius)
        self._rect.radius = [r, r, r, r]

        # Гарантируем, что перед началом рендеринга букв Kivy увидит чистый цвет
        self._ctx_reset.rgba = (1, 1, 1, 1)

        # Принудительно будим каретку Windows/Android
        if hasattr(self, '_trigger_cursor_blink'):
            self._trigger_cursor_blink()


class SpinnerOptionMaterial(SpinnerOption):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", POPUP_SURFACE)
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)


class MaterialSpinner(Spinner):
    def __init__(self, radius=dp(24), **kwargs):
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_color", TRANSPARENT_APP)
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("color", TEXT_PRIMARY)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        kwargs.setdefault("option_cls", SpinnerOptionMaterial)
        super().__init__(**kwargs)
        self.radius = radius

        with self.canvas.before:
            self._fill = Color(*INPUT_FILL)
            self._rect = RoundedRectangle(radius=[0])
            self._text_pass = Color(1, 1, 1, 1)

        # focus удален, чтобы не вызывать ошибку KeyError
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_canvas(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        r = _capsule_radius(self.size, self.radius)
        self._rect.radius = [r, r, r, r]


class Chip(Label):
    def __init__(self, fill_color=M3_SURFACE_VARIANT, border_color=M3_OUTLINE, text_color=TEXT_SECONDARY, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(26))
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("color", text_color)
        super().__init__(**kwargs)
        self.fill_color = fill_color
        self.border_color = border_color
        self.radius = dp(20)
        with self.canvas.before:
            self._fill = Color(*self.fill_color)
            self._rect = RoundedRectangle(radius=[0])
        self.bind(texture_size=self._update_size, text=self._update_size, pos=self._update_canvas,
                  size=self._update_canvas)
        Clock.schedule_once(self._update_size, 0)

    def _update_size(self, *_):
        self.width = max(dp(70), self.texture_size[0] + dp(20))
        self._update_canvas()

    def _update_canvas(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size
        r = _capsule_radius(self.size, self.radius)
        self._rect.radius = [r, r, r, r]


class CircleButton(MaterialButton):
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("width", dp(58))
        kwargs.setdefault("height", dp(58))
        kwargs.setdefault("radius", dp(29))
        kwargs.setdefault("font_size", "24sp")
        kwargs.setdefault("bold", True)
        super().__init__(**kwargs)


class IconCircleButton(CircleButton):
    def __init__(self, icon_source=None, fallback_text="", **kwargs):
        kwargs.setdefault("text", fallback_text)
        super().__init__(**kwargs)
        self._icon = None
        with self.canvas.before:
            self._bg_color = Color(*self.fill_color)
            self._bg = Ellipse(
                pos=self.pos,
                size=self.size
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        if icon_source:
            path = Path(icon_source)
            if path.exists():
                self.text = ""
                self._icon = Image(source=str(path))
                if hasattr(self._icon, "fit_mode"):
                    self._icon.fit_mode = "contain"
                self.add_widget(self._icon)
                self.bind(pos=self._update_icon, size=self._update_icon)
                Clock.schedule_once(self._update_icon, 0)
        Clock.schedule_once(self._update_canvas, 0)

    def _update_icon(self, *_):
        if self._icon is None:
            return
        pad = dp(7)
        max_icon = min(self.width - pad * 2, self.height - pad * 2)
        base_side = max(max_icon * 0.7, dp(8))
        icon_side = min(base_side * 1.25, max_icon)
        self._icon.size = (icon_side, icon_side)
        self._icon.pos = (
            self.x + (self.width - icon_side) / 2,
            self.y + (self.height - icon_side) / 2,
        )

    def _update_canvas(self, *_):
        super()._update_canvas()

        self._bg.pos = self.pos
        self._bg.size = self.size


class MaterialLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_NAME)
        kwargs.setdefault("font_size", FONT_SIZE)
        kwargs.setdefault("bold", True)
        kwargs.setdefault("color", TEXT_PRIMARY)
        super().__init__(**kwargs)