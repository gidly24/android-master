from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from models import CATEGORIES, PRIORITY_OPTIONS, RECURRENCE_OPTIONS
from ui.components import (
    DangerGlassButton,
    GlassPane,
    GlassSpinner,
    GlassTextInput,
    PrimaryGlassButton,
    TEXT_PRIMARY,
    bind_auto_height,
    bind_text_size,
)


class TaskFormPopup(Popup):
    """Popup window for creating and editing tasks."""

    def __init__(self, on_save, task=None, **kwargs):
        kwargs.setdefault("title", "Редактирование задачи" if task else "Новая задача")
        kwargs.setdefault("size_hint", (0.94, 0.94))
        kwargs.setdefault("separator_height", 1)
        kwargs.setdefault("separator_color", (0.26, 0.34, 0.52, 1))
        kwargs.setdefault("title_color", TEXT_PRIMARY)
        kwargs.setdefault("background_color", (0.05, 0.07, 0.11, 1))
        super().__init__(**kwargs)

        self.on_save = on_save
        self.task = task
        self.content = self._build_content()

        if task:
            self._fill_data(task)

    def _build_content(self):
        root = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(12),
            fill_color=(0.08, 0.11, 0.18, 1),
            border_color=(0.28, 0.37, 0.56, 0.95),
        )

        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))

        self.title_input = GlassTextInput(multiline=False, hint_text="Введите название задачи")
        self.description_input = GlassTextInput(
            multiline=True,
            height=dp(120),
            hint_text="Краткое описание или комментарий",
        )
        self.category_spinner = GlassSpinner(text=CATEGORIES[0], values=tuple(CATEGORIES))
        self.due_date_input = GlassTextInput(multiline=False, hint_text="Например: 2026-03-20")
        self.recurrence_spinner = GlassSpinner(text=RECURRENCE_OPTIONS[0], values=tuple(RECURRENCE_OPTIONS))
        self.priority_spinner = GlassSpinner(text=PRIORITY_OPTIONS[1], values=tuple(PRIORITY_OPTIONS))

        form.add_widget(self._build_field("Название", self.title_input))
        form.add_widget(self._build_field("Описание", self.description_input))
        form.add_widget(self._build_field("Категория", self.category_spinner))
        form.add_widget(self._build_field("Дата ближайшего выполнения", self.due_date_input))
        form.add_widget(self._build_field("Периодичность", self.recurrence_spinner))
        form.add_widget(self._build_field("Приоритет", self.priority_spinner))

        self.message_label = Label(
            text="",
            color=(1, 0.56, 0.6, 1),
            size_hint_y=None,
            height=dp(26),
            halign="left",
            valign="middle",
        )
        bind_text_size(self.message_label)
        form.add_widget(self.message_label)

        scroll.add_widget(form)
        root.add_widget(scroll)

        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        cancel_button = DangerGlassButton(text="Отмена")
        cancel_button.bind(on_release=lambda *_: self.dismiss())

        save_button = PrimaryGlassButton(text="Сохранить")
        save_button.bind(on_release=lambda *_: self._handle_save())

        buttons.add_widget(cancel_button)
        buttons.add_widget(save_button)
        root.add_widget(buttons)
        return root

    @staticmethod
    def _build_field(label_text, widget):
        container = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        title = Label(
            text=label_text,
            color=TEXT_PRIMARY,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(22), extra=dp(4))

        container.add_widget(title)
        container.add_widget(widget)
        container.bind(minimum_height=container.setter("height"))
        return container

    def _fill_data(self, task):
        self.title_input.text = task.title
        self.description_input.text = task.description
        self.category_spinner.text = task.category
        self.due_date_input.text = task.due_date
        self.recurrence_spinner.text = task.recurrence
        self.priority_spinner.text = task.priority

    def _handle_save(self):
        task_data = {
            "title": self.title_input.text,
            "description": self.description_input.text,
            "category": self.category_spinner.text,
            "due_date": self.due_date_input.text.strip(),
            "recurrence": self.recurrence_spinner.text,
            "priority": self.priority_spinner.text,
            "status": self.task.status if self.task else "активна",
        }

        try:
            self.on_save(task_data, self.task.id if self.task else None)
        except ValueError as error:
            self.message_label.text = str(error)
            return

        self.dismiss()
