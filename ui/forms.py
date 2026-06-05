from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView

from models import CATEGORIES, PRIORITY_OPTIONS, RECURRENCE_OPTIONS
from ui.android_pickers import open_date_picker, open_time_picker
from ui.components import (
    APP_BACKGROUND,
    FONT_NAME,
    FONT_SIZE,
    POPUP_SURFACE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TRANSPARENT_APP,
    DangerButton,
    FilledButton,
    MaterialButton,
    MaterialLabel as Label,
    MaterialCard,
    MaterialSpinner,
    MaterialTextInput,
    bind_auto_height,
    bind_text_size,
)


class TaskFormPopup(ModalView):
    def __init__(self, on_save, task=None, **kwargs):
        kwargs.setdefault("size_hint", (0.92, 0.92))
        kwargs.setdefault("auto_dismiss", False)
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", TRANSPARENT_APP)
        super().__init__(**kwargs)
        self.overlay_color = (APP_BACKGROUND[0], APP_BACKGROUND[1], APP_BACKGROUND[2], 0.35)
        self.on_save = on_save
        self.task = task
        self.title_text = "Редактирование задачи" if task else "Новая задача"
        self.add_widget(self._build_content())
        if task:
            self._fill_data()

    def _build_content(self):
        root = MaterialCard(
            orientation="vertical",
            spacing=dp(16),
            padding=dp(16),
            fill_color=POPUP_SURFACE,
        )

        title = Label(
            text=self.title_text,
            color=TEXT_PRIMARY,
            font_name=FONT_NAME,
            font_size=FONT_SIZE,
            bold=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(28), extra=dp(2))
        root.add_widget(title)

        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(16), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.title_input = MaterialTextInput(multiline=False, hint_text="Название задачи")
        self.description_input = MaterialTextInput(multiline=True, height=dp(110), hint_text="Описание")
        self.category_spinner = MaterialSpinner(
            text=CATEGORIES[0].capitalize(),
            values=tuple(value.capitalize() for value in CATEGORIES),
        )
        self.due_date_input = MaterialTextInput(multiline=False, hint_text="Дата (YYYY-MM-DD), можно пусто")
        self.due_time_input = MaterialTextInput(multiline=False, hint_text="Время (HH:MM), можно пусто")
        self.recurrence_spinner = MaterialSpinner(
            text=RECURRENCE_OPTIONS[0].capitalize(),
            values=tuple(value.capitalize() for value in RECURRENCE_OPTIONS),
        )
        self.priority_spinner = MaterialSpinner(
            text=PRIORITY_OPTIONS[1].capitalize(),
            values=tuple(value.capitalize() for value in PRIORITY_OPTIONS),
        )

        form.add_widget(self._field("Название", self.title_input))
        form.add_widget(self._field("Описание", self.description_input))
        form.add_widget(self._field("Категория", self.category_spinner))
        form.add_widget(self._field("Дата дедлайна", self._date_field()))
        form.add_widget(self._field("Время дедлайна", self._time_field()))
        form.add_widget(self._field("Периодичность", self.recurrence_spinner))
        form.add_widget(self._field("Приоритет", self.priority_spinner))

        self.error_label = Label(
            text="",
            color=TEXT_PRIMARY,
            font_size=FONT_SIZE,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(self.error_label)
        bind_auto_height(self.error_label, min_height=dp(24), extra=dp(2))
        form.add_widget(self.error_label)

        tip = Label(
            text="Если указываете время, дата должна быть заполнена.",
            color=TEXT_MUTED,
            font_name=FONT_NAME,
            font_size=FONT_SIZE,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(tip)
        bind_auto_height(tip, min_height=dp(24), extra=dp(2))
        form.add_widget(tip)

        scroll.add_widget(form)
        root.add_widget(scroll)

        actions = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        cancel = DangerButton(text="Отмена", height=dp(44))
        cancel.bind(on_release=lambda *_: self.dismiss())
        save = FilledButton(text="Сохранить", height=dp(44))
        save.bind(on_release=lambda *_: self._save())
        actions.add_widget(cancel)
        actions.add_widget(save)
        root.add_widget(actions)
        return root

    @staticmethod
    def _field(text, widget):
        box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        title = Label(
            text=text,
            color=TEXT_PRIMARY,
            font_size=FONT_SIZE,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(20), extra=dp(2))
        box.add_widget(title)
        box.add_widget(widget)
        box.bind(minimum_height=box.setter("height"))
        return box

    def _date_field(self):
        row = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(46))
        pick = MaterialButton(text="Выбрать", size_hint_x=None, width=dp(110))
        clear = MaterialButton(text="Очистить", size_hint_x=None, width=dp(110))
        pick.bind(on_release=lambda *_: self._open_date_picker())
        clear.bind(on_release=lambda *_: self._clear_date())
        row.add_widget(self.due_date_input)
        row.add_widget(pick)
        row.add_widget(clear)
        return row

    def _time_field(self):
        row = BoxLayout(orientation="horizontal", spacing=dp(6), size_hint_y=None, height=dp(46))
        pick = MaterialButton(text="Выбрать", size_hint_x=None, width=dp(110))
        clear = MaterialButton(text="Очистить", size_hint_x=None, width=dp(110))
        pick.bind(on_release=lambda *_: self._open_time_picker())
        clear.bind(on_release=lambda *_: self._clear_time())
        row.add_widget(self.due_time_input)
        row.add_widget(pick)
        row.add_widget(clear)
        return row

    def _open_date_picker(self):
        opened = open_date_picker(
            initial_date=self.due_date_input.text.strip(),
            on_select=self._on_date_selected,
        )
        if not opened:
            self.error_label.text = "Выбор даты доступен на Android. Здесь используйте ручной ввод."

    def _open_time_picker(self):
        opened = open_time_picker(
            initial_time=self.due_time_input.text.strip(),
            on_select=self._on_time_selected,
        )
        if not opened:
            self.error_label.text = "Выбор времени доступен на Android. Здесь используйте ручной ввод."

    def _on_date_selected(self, selected_date):
        self.error_label.text = ""
        self.due_date_input.text = selected_date or ""

    def _on_time_selected(self, selected_time):
        self.error_label.text = ""
        self.due_time_input.text = selected_time or ""

    def _clear_date(self):
        self.due_date_input.text = ""
        self.error_label.text = ""

    def _clear_time(self):
        self.due_time_input.text = ""
        self.error_label.text = ""

    def _fill_data(self):
        self.title_input.text = self.task.title or ""
        self.description_input.text = self.task.description or ""
        self.category_spinner.text = (self.task.category or CATEGORIES[0]).capitalize()
        self.due_date_input.text = self.task.due_date or ""
        self.due_time_input.text = self.task.due_time or ""
        self.recurrence_spinner.text = (self.task.recurrence or RECURRENCE_OPTIONS[0]).capitalize()
        self.priority_spinner.text = (self.task.priority or PRIORITY_OPTIONS[1]).capitalize()

    def _save(self):
        recurrence = self.recurrence_spinner.text.lower()
        due_date = self.due_date_input.text.strip()
        if recurrence != "одноразовая" and not due_date:
            from datetime import date
            self.due_date_input.text = date.today().isoformat()
        task_data = {
            "title": self.title_input.text.strip().capitalize(),
            "description": self.description_input.text,
            "category": self.category_spinner.text,
            "due_date": self.due_date_input.text.strip(),
            "due_time": self.due_time_input.text.strip(),
            "recurrence": self.recurrence_spinner.text,
            "priority": self.priority_spinner.text,
            "status": self.task.status if self.task else "активна",
        }
        try:
            self.on_save(task_data, self.task.id if self.task else None)
        except ValueError as error:
            self.error_label.text = str(error)
            return
        self.dismiss()
