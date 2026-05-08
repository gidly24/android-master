from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from ui.components import (
    APP_BACKGROUND,
    FONT_SIZE,
    INPUT_FILL,
    M3_PRIMARY,
    POPUP_SURFACE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TRANSPARENT_APP,
    FilledButton,
    MaterialButton,
    MaterialCard,
    MaterialLabel as Label,
    MaterialTextInput,
    bind_auto_height,
    bind_text_size,
)


class ChatBubble(MaterialCard):
    def __init__(self, role: str, text: str, **kwargs):
        user = role == "user"
        super().__init__(
            orientation="vertical",
            size_hint=(0.9, None),
            spacing=dp(4),
            padding=(dp(10), dp(8), dp(10), dp(8)),
            fill_color=M3_PRIMARY if user else INPUT_FILL,
            border_color=M3_PRIMARY if user else INPUT_FILL,
            **kwargs,
        )
        self.bind(minimum_height=self.setter("height"))
        title = Label(
            text="Вы" if user else "Ассистент",
            color=TEXT_PRIMARY if user else TEXT_MUTED,
            size_hint_y=None,
            font_size=FONT_SIZE,
            bold=True,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(18), extra=dp(2))
        body = Label(
            text=text,
            color=TEXT_PRIMARY,
            size_hint_y=None,
            font_size=FONT_SIZE,
            halign="left",
            valign="top",
        )
        bind_text_size(body)
        bind_auto_height(body, min_height=dp(20), extra=dp(2))
        self.add_widget(title)
        self.add_widget(body)


class ChatModal(ModalView):
    def __init__(self, agent, on_tasks_changed=None, **kwargs):
        kwargs.setdefault("size_hint", (0.94, 0.94))
        kwargs.setdefault("auto_dismiss", True)
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", TRANSPARENT_APP)
        super().__init__(**kwargs)
        self.overlay_color = (APP_BACKGROUND[0], APP_BACKGROUND[1], APP_BACKGROUND[2], 0.45)

        self.agent = agent
        self.on_tasks_changed = on_tasks_changed
        self.history = []
        self._busy = False
        self._build_ui()
        self._append_message("assistant", "Что нужно сделать с задачами?")

    def _build_ui(self):
        root = MaterialCard(
            orientation="vertical",
            spacing=dp(8),
            padding=(dp(10), dp(10), dp(10), dp(10)),
            fill_color=POPUP_SURFACE,
        )

        title_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
        title = Label(text="AI чат", color=TEXT_PRIMARY, font_size=FONT_SIZE, bold=True, halign="left", valign="middle")
        title.bind(size=lambda *_: setattr(title, "text_size", title.size))
        close_btn = MaterialButton(text="Закрыть", size_hint_x=None, width=dp(82), height=dp(36))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        title_row.add_widget(title)
        title_row.add_widget(close_btn)
        root.add_widget(title_row)

        self.scroll = ScrollView()
        self.messages = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=(0, 0, 0, dp(6)))
        self.messages.bind(minimum_height=self.messages.setter("height"))
        self.scroll.add_widget(self.messages)
        root.add_widget(self.scroll)

        self.status = Label(text="", color=TEXT_MUTED, font_size=FONT_SIZE, size_hint_y=None, height=dp(14), halign="left", valign="middle")
        bind_text_size(self.status)
        root.add_widget(self.status)

        composer = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.input = MaterialTextInput(multiline=False, hint_text="Введите запрос", height=dp(46))
        self.input.bind(on_text_validate=lambda *_: self.send_message())
        self.send_btn = FilledButton(text="Отправить", height=dp(46), size_hint_x=None, width=dp(108))
        self.send_btn.bind(on_release=lambda *_: self.send_message())
        composer.add_widget(self.input)
        composer.add_widget(self.send_btn)
        root.add_widget(composer)
        self.add_widget(root)

    def send_message(self, preset_text=None):
        if self._busy:
            return
        text = (preset_text if preset_text is not None else self.input.text).strip()
        if not text:
            return
        self.input.text = ""
        self._append_message("user", text)
        self._set_busy(True, "Обрабатываю...")
        Thread(target=self._worker, args=(text,), daemon=True).start()

    def _worker(self, text):
        try:
            reply = self.agent.process_message(text, history=self.history)
            Clock.schedule_once(lambda *_: self._on_reply(reply), 0)
        except Exception:
            Clock.schedule_once(lambda *_: self._on_error(), 0)

    def _on_reply(self, reply):
        self._append_message("assistant", reply.answer, buttons=reply.ui_hints.get("buttons", []))
        self._set_busy(False, "")
        if reply.should_refresh and self.on_tasks_changed:
            self.on_tasks_changed()

    def _on_error(self):
        self._append_message("assistant", "Ошибка обработки запроса. Попробуйте еще раз.")
        self._set_busy(False, "")

    def _set_busy(self, busy, message):
        self._busy = busy
        self.input.disabled = busy
        self.send_btn.disabled = busy
        self.status.text = message

    def _append_message(self, role, text, buttons=None):
        self.history.append({"role": role, "content": text})
        row = BoxLayout(size_hint_y=None)
        row.bind(minimum_height=row.setter("height"))
        if role == "assistant":
            bubble_box = BoxLayout(orientation="vertical", size_hint=(0.9, None), spacing=dp(6))
            bubble_box.bind(minimum_height=bubble_box.setter("height"))
            bubble_box.add_widget(ChatBubble(role=role, text=text))
            if buttons:
                for data in buttons:
                    btn = MaterialButton(text=data["label"], height=dp(36), font_size=FONT_SIZE)
                    btn.bind(on_release=lambda *_, msg=data["message"]: self.send_message(msg))
                    bubble_box.add_widget(btn)
            row.add_widget(bubble_box)
            row.add_widget(Widget())
        else:
            row.add_widget(Widget())
            row.add_widget(ChatBubble(role=role, text=text))
        self.messages.add_widget(row)
        Clock.schedule_once(self._scroll_bottom, 0.05)

    def _scroll_bottom(self, *_):
        self.scroll.scroll_y = 0
