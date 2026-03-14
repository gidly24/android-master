from calendar import monthcalendar
from datetime import date as date_cls

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView

from models import CATEGORIES, PRIORITY_OPTIONS, RECURRENCE_OPTIONS
from ui.components import (
    DangerGlassButton,
    GlassPane,
    GlassSpinner,
    GlassTextInput,
    GlassButton,
    PrimaryGlassButton,
    TEXT_MUTED,
    TEXT_PRIMARY,
    bind_auto_height,
    bind_text_size,
)


class TaskFormPopup(ModalView):
    """Modal window for creating and editing tasks."""

    def __init__(self, on_save, task=None, **kwargs):
        kwargs.setdefault("size_hint", (0.92, 0.92))
        kwargs.setdefault("auto_dismiss", False)
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        super().__init__(**kwargs)

        self.on_save = on_save
        self.task = task
        self.form_title = "Редактирование задачи" if task else "Новая задача"
        self.overlay_color = (0.1, 0.13, 0.2, 0.24)
        self.add_widget(self._build_content())

        if task:
            self._fill_data(task)

    def _build_content(self):
        root = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(16), dp(18), dp(16), dp(16)),
            fill_color=(1, 1, 1, 1),
            border_color=(0.85, 0.87, 0.91, 1),
            radius=dp(30),
        )

        header = Label(
            text=self.form_title,
            color=TEXT_PRIMARY,
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(header)
        bind_auto_height(header, min_height=dp(30), extra=dp(4))
        root.add_widget(header)

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
        self.due_date_input = GlassTextInput(
            multiline=False,
            hint_text="Выберите дату",
            readonly=True,
        )
        self.date_picker_button = GlassButton(
            text="Календарь",
            size_hint_x=None,
            width=dp(112),
            height=dp(50),
        )
        self.date_picker_button.bind(on_release=lambda *_: self.open_calendar())
        self.recurrence_spinner = GlassSpinner(text=RECURRENCE_OPTIONS[0], values=tuple(RECURRENCE_OPTIONS))
        self.priority_spinner = GlassSpinner(text=PRIORITY_OPTIONS[1], values=tuple(PRIORITY_OPTIONS))

        form.add_widget(self._build_field("Название", self.title_input))
        form.add_widget(self._build_field("Описание", self.description_input))
        form.add_widget(self._build_field("Категория", self.category_spinner))
        form.add_widget(self._build_date_field())
        form.add_widget(self._build_field("Периодичность", self.recurrence_spinner))
        form.add_widget(self._build_field("Приоритет", self.priority_spinner))

        self.message_label = Label(
            text="",
            color=(0.9, 0.32, 0.39, 1),
            size_hint_y=None,
            height=dp(28),
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

    def _build_date_field(self):
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        row.add_widget(self.due_date_input)
        row.add_widget(self.date_picker_button)
        return self._build_field("Дата ближайшего выполнения", row)

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

    def open_calendar(self):
        selected_date = self.due_date_input.text.strip() or date_cls.today().isoformat()
        popup = CalendarPickerModal(initial_date=selected_date, on_select=self.set_due_date)
        popup.open()

    def set_due_date(self, value):
        self.due_date_input.text = value


class CalendarPickerModal(ModalView):
    """Simple built-in calendar picker for task due dates."""

    WEEKDAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    MONTH_NAMES = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }

    def __init__(self, initial_date: str, on_select, **kwargs):
        kwargs.setdefault("size_hint", (0.9, None))
        kwargs.setdefault("height", dp(520))
        kwargs.setdefault("auto_dismiss", True)
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        super().__init__(**kwargs)

        self.overlay_color = (0.1, 0.13, 0.2, 0.24)
        self.on_select = on_select
        self.current_date = date_cls.fromisoformat(initial_date)
        self.display_year = self.current_date.year
        self.display_month = self.current_date.month

        self.content_box = self._build_content()
        self.add_widget(self.content_box)
        self.refresh_days()

    def _build_content(self):
        root = GlassPane(
            orientation="vertical",
            spacing=dp(12),
            padding=(dp(16), dp(18), dp(16), dp(16)),
            fill_color=(1, 1, 1, 1),
            border_color=(0.85, 0.87, 0.91, 1),
            radius=dp(30),
        )

        title = Label(
            text="Выбор даты",
            color=TEXT_PRIMARY,
            font_size="20sp",
            bold=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(30), extra=dp(4))
        root.add_widget(title)

        header = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        prev_button = GlassButton(text="<", size_hint_x=None, width=dp(44), height=dp(44))
        prev_button.bind(on_release=lambda *_: self.shift_month(-1))

        self.month_label = Label(
            color=TEXT_PRIMARY,
            font_size="17sp",
            bold=True,
            halign="center",
            valign="middle",
        )
        bind_text_size(self.month_label)

        self.year_spinner = GlassSpinner(
            text=str(self.display_year),
            values=tuple(str(year) for year in range(self.display_year - 10, self.display_year + 11)),
            size_hint_x=None,
            width=dp(116),
            height=dp(44),
        )
        self.year_spinner.bind(text=self.on_year_selected)

        next_button = GlassButton(text=">", size_hint_x=None, width=dp(44), height=dp(44))
        next_button.bind(on_release=lambda *_: self.shift_month(1))

        header.add_widget(prev_button)
        header.add_widget(self.month_label)
        header.add_widget(self.year_spinner)
        header.add_widget(next_button)
        root.add_widget(header)

        weekdays = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(4))
        for day_name in self.WEEKDAY_NAMES:
            label = Label(
                text=day_name,
                color=TEXT_MUTED,
                font_size="13sp",
                bold=True,
            )
            weekdays.add_widget(label)
        root.add_widget(weekdays)

        self.days_box = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            size_hint_y=None,
            height=dp(282),
        )
        root.add_widget(self.days_box)

        footer = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        cancel_button = GlassButton(text="Отмена", height=dp(46))
        cancel_button.bind(on_release=lambda *_: self.dismiss())

        today_button = PrimaryGlassButton(text="Сегодня", height=dp(46))
        today_button.bind(on_release=lambda *_: self.pick_today())

        footer.add_widget(cancel_button)
        footer.add_widget(today_button)
        root.add_widget(footer)
        return root

    def refresh_days(self):
        self.month_label.text = self.MONTH_NAMES[self.display_month]
        self.year_spinner.text = str(self.display_year)
        self.days_box.clear_widgets()

        month_rows = monthcalendar(self.display_year, self.display_month)
        while len(month_rows) < 6:
            month_rows.append([0] * 7)

        for week in month_rows:
            row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(4))
            for day_number in week:
                if day_number == 0:
                    row.add_widget(Label(text=""))
                    continue

                current = date_cls(self.display_year, self.display_month, day_number)
                button = self._create_day_button(current)
                row.add_widget(button)
            self.days_box.add_widget(row)

    def _create_day_button(self, current: date_cls):
        is_selected = current == self.current_date
        if is_selected:
            button = PrimaryGlassButton(
                text=str(current.day),
                height=dp(42),
                radius=dp(18),
            )
        else:
            button = GlassButton(
                text=str(current.day),
                height=dp(42),
                radius=dp(18),
            )
        button.bind(on_release=lambda *_: self.select_date(current))
        return button

    def shift_month(self, delta: int):
        month = self.display_month + delta
        year = self.display_year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self.display_month = month
        self.display_year = year
        self._sync_year_values()
        self.refresh_days()

    def on_year_selected(self, *_):
        try:
            self.display_year = int(self.year_spinner.text)
        except ValueError:
            return
        self._sync_year_values()
        self.refresh_days()

    def select_date(self, value: date_cls):
        self.current_date = value
        self.on_select(value.isoformat())
        self.dismiss()

    def pick_today(self):
        today = date_cls.today()
        self.current_date = today
        self.on_select(today.isoformat())
        self.dismiss()

    def _sync_year_values(self):
        self.year_spinner.values = tuple(
            str(year) for year in range(self.display_year - 10, self.display_year + 11)
        )
