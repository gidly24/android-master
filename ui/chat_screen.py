from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from ui.components import FONT_SIZE, GlassButton, GlassPane, GlassTextInput, TEXT_MUTED, TEXT_PRIMARY, bind_auto_height, bind_text_size


class ChatBubble(GlassPane):
    def __init__(self, role: str, text: str, **kwargs):
        is_user = role == "user"
        super().__init__(
            orientation="vertical",
            size_hint=(0.9, None),
            padding=(dp(12), dp(10), dp(12), dp(10)),
            spacing=dp(6),
            fill_color=(0.33, 0.66, 0.95, 1) if is_user else (1, 1, 1, 0.98),
            border_color=(0.33, 0.66, 0.95, 1) if is_user else (0.84, 0.87, 0.92, 1),
            **kwargs,
        )
        self.bind(minimum_height=self.setter("height"))

        title = Label(
            text="Вы" if is_user else "Ассистент",
            color=(1, 1, 1, 0.95) if is_user else TEXT_MUTED,
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
            color=(1, 1, 1, 1) if is_user else TEXT_PRIMARY,
            size_hint_y=None,
            font_size=FONT_SIZE,
            halign="left",
            valign="top",
        )
        bind_text_size(body)
        bind_auto_height(body, min_height=dp(22), extra=dp(4))

        self.add_widget(title)
        self.add_widget(body)


class ChatScreen(Screen):
    AUTO_CLEAR_SECONDS = 30 * 60
    QUICK_ACTIONS = [
        ("Создать", "добавь задачу"),
        ("Удалить", "удали задачу"),
        ("Изменить", "измени задачу"),
        ("Выполнить", "отметь задачу как выполненную"),
        ("Показать", "покажи все задачи"),
        ("Статистика", "сколько у меня просроченных дел?"),
    ]

    def __init__(self, agent, on_tasks_changed=None, **kwargs):
        super().__init__(**kwargs)
        self.agent = agent
        self.on_tasks_changed = on_tasks_changed
        self.history: list[dict[str, str]] = []
        self._auto_clear_event = None
        self._request_in_progress = False
        self._build_ui()
        self._reset_chat_session()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(12))

        self.status_panel = GlassPane(
            orientation="vertical",
            spacing=dp(4),
            padding=(dp(12), dp(10), dp(12), dp(10)),
            size_hint_y=None,
            height=0,
            opacity=0,
        )
        self.status_mode_label = Label(
            text="",
            color=TEXT_PRIMARY,
            size_hint_y=None,
            font_size=FONT_SIZE,
            bold=True,
            halign="left",
            valign="middle",
        )
        bind_text_size(self.status_mode_label)
        bind_auto_height(self.status_mode_label, min_height=dp(18), extra=dp(2))
        self.status_step_label = Label(
            text="",
            color=TEXT_MUTED,
            size_hint_y=None,
            font_size=FONT_SIZE,
            halign="left",
            valign="middle",
        )
        bind_text_size(self.status_step_label)
        bind_auto_height(self.status_step_label, min_height=dp(18), extra=dp(2))
        self.status_panel.add_widget(self.status_mode_label)
        self.status_panel.add_widget(self.status_step_label)
        root.add_widget(self.status_panel)

        history_panel = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(12), dp(12), dp(12), dp(12)),
        )
        self.scroll_view = ScrollView(bar_width=dp(4), scroll_type=["bars", "content"])
        self.messages_box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            padding=(0, 0, 0, dp(6)),
        )
        self.messages_box.bind(minimum_height=self.messages_box.setter("height"))
        self.scroll_view.add_widget(self.messages_box)
        history_panel.add_widget(self.scroll_view)
        root.add_widget(history_panel)

        composer = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(12), dp(12), dp(12), dp(12)),
            size_hint_y=None,
        )
        composer.bind(minimum_height=composer.setter("height"))
        input_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.input = GlassTextInput(
            hint_text="Напиши команду обычной фразой",
            multiline=False,
            height=dp(48),
            input_type="text",
            keyboard_suggestions=True,
        )
        self.input.bind(on_text_validate=lambda *_: self.send_message())
        self.status_label = Label(
            text="",
            color=TEXT_MUTED,
            font_size=FONT_SIZE,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
        )
        bind_text_size(self.status_label)
        self.send_button = GlassButton(text=">", height=dp(48), size_hint_x=None, width=dp(48), font_size="18sp")
        self.send_button.bind(on_release=lambda *_: self.send_message())
        input_row.add_widget(self.input)
        input_row.add_widget(self.send_button)

        composer.add_widget(input_row)
        composer.add_widget(self.status_label)
        root.add_widget(composer)
        self.add_widget(root)

    def send_message(self, preset_text: str | None = None):
        if self._request_in_progress:
            return

        text = (preset_text if preset_text is not None else self.input.text).strip()
        if not text:
            return

        self.input.text = ""
        self._append_message("user", text)
        self._set_busy(True, "Обрабатываю запрос...")

        Thread(target=self._process_message_worker, args=(text,), daemon=True).start()

    def _process_message_worker(self, text: str):
        try:
            reply = self.agent.process_message(text, history=self.history)
        except Exception:
            Clock.schedule_once(
                lambda *_: self._handle_reply_error(
                    "Не удалось обработать запрос. Проверь подключение к API или попробуй переформулировать."
                ),
                0,
            )
            return

        Clock.schedule_once(lambda *_: self._handle_reply_success(reply), 0)

    def _handle_reply_success(self, reply):
        self._append_message(
            "assistant",
            reply.answer,
            buttons=reply.ui_hints.get("buttons", []),
            draft=reply.ui_hints.get("draft", {}),
        )
        self._set_status(reply.ui_hints.get("status", {}))
        self._set_busy(False, "")
        if reply.should_refresh and self.on_tasks_changed is not None:
            self.on_tasks_changed()

    def _handle_reply_error(self, message: str):
        fallback_buttons = list(self.agent.dispatcher.MAIN_MENU_BUTTONS)
        self._append_message("assistant", message, buttons=fallback_buttons)
        self._set_status({})
        self._set_busy(False, "")

    def _set_busy(self, busy: bool, status: str):
        self._request_in_progress = busy
        self.input.disabled = busy
        self.send_button.disabled = busy
        self.status_label.text = status

    def _append_message(
        self,
        role: str,
        text: str,
        buttons: list[dict[str, str]] | None = None,
        draft: dict[str, str] | None = None,
    ):
        self.history.append({"role": role, "content": text})
        self._schedule_auto_clear()

        row = BoxLayout(size_hint_y=None, padding=(0, 0, 0, 0))
        row.bind(minimum_height=row.setter("height"))
        if role == "assistant":
            assistant_box = BoxLayout(orientation="vertical", size_hint=(0.9, None), spacing=dp(6))
            assistant_box.bind(minimum_height=assistant_box.setter("height"))
            assistant_box.add_widget(ChatBubble(role=role, text=text))
            if draft:
                assistant_box.add_widget(self._build_draft_preview(draft))
            if buttons:
                assistant_box.add_widget(self._build_inline_buttons(buttons))
            row.add_widget(assistant_box)
            row.add_widget(Widget())
        else:
            row.add_widget(Widget())
            row.add_widget(ChatBubble(role=role, text=text))

        self.messages_box.add_widget(row)
        Clock.schedule_once(self._scroll_to_bottom, 0.05)

    def _scroll_to_bottom(self, *_):
        self.scroll_view.scroll_y = 0

    def _build_inline_buttons(self, buttons: list[dict[str, str]]):
        container = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        container.bind(minimum_height=container.setter("height"))
        rows = [buttons[i : i + 1] for i in range(0, len(buttons), 1)]
        for row_buttons in rows:
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            for button_data in row_buttons:
                button = GlassButton(
                    text=button_data["label"],
                    height=dp(40),
                    font_size="12sp",
                    halign="center",
                    valign="middle",
                )
                button.bind(width=lambda instance, value: setattr(instance, "text_size", (max(value - dp(16), dp(40)), None)))
                button.bind(on_release=lambda *_ , message=button_data["message"]: self.send_message(message))
                row.add_widget(button)
            container.add_widget(row)
        return container

    def _build_draft_preview(self, draft: dict[str, str]):
        pane = GlassPane(
            orientation="vertical",
            spacing=dp(4),
            padding=(dp(10), dp(8), dp(10), dp(8)),
            size_hint_y=None,
            fill_color=(0.96, 0.97, 0.99, 1),
            border_color=(0.84, 0.87, 0.92, 1),
        )
        pane.bind(minimum_height=pane.setter("height"))
        for label, value in draft.items():
            line = Label(
                text=f"{label}: {value}",
                color=TEXT_PRIMARY,
                size_hint_y=None,
                font_size="12sp",
                halign="left",
                valign="middle",
            )
            bind_text_size(line)
            bind_auto_height(line, min_height=dp(18), extra=dp(2))
            pane.add_widget(line)
        return pane

    def _set_status(self, status: dict[str, str]):
        if not status:
            self.status_panel.height = 0
            self.status_panel.opacity = 0
            self.status_mode_label.text = ""
            self.status_step_label.text = ""
            return
        mode = status.get("mode", "")
        step = status.get("step", "")
        waiting = status.get("waiting", "")
        self.status_mode_label.text = mode
        self.status_step_label.text = " • ".join(part for part in (step, waiting) if part)
        self.status_panel.height = dp(62)
        self.status_panel.opacity = 1

    def _schedule_auto_clear(self):
        if self._auto_clear_event is not None:
            self._auto_clear_event.cancel()
        self._auto_clear_event = Clock.schedule_once(self._auto_clear_chat, self.AUTO_CLEAR_SECONDS)

    def _auto_clear_chat(self, *_):
        self._auto_clear_event = None
        if self._request_in_progress:
            self._schedule_auto_clear()
            return
        self._reset_chat_session(expired=True)

    def _reset_chat_session(self, expired: bool = False):
        self.history = []
        self.messages_box.clear_widgets()
        self._set_status({})
        if expired:
            self._append_message(
                "assistant",
                "Диалог очищен автоматически после 30 минут бездействия.",
            )
        self._append_message(
            "assistant",
            "Что нужно сделать с задачами?",
            buttons=list(self.agent.dispatcher.MAIN_MENU_BUTTONS),
        )
