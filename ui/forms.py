from calendar import monthcalendar
from datetime import date as date_cls

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView

from ui.android_pickers import open_date_picker, open_time_picker

from models import CATEGORIES, PRIORITY_OPTIONS, RECURRENCE_OPTIONS
from ui.components import (
    DangerGlassButton,
    FONT_SIZE,
    GlassPane,
    GlassSpinner,
    GlassTextInput,
    GlassButton,
    IOSSwitch,
    PrimaryGlassButton,
    TEXT_MUTED,
    TEXT_PRIMARY,
    bind_auto_height,
    bind_text_size,
)


class PickerTextInput(GlassTextInput):
    """Readonly input that opens a picker on tap."""

    def __init__(self, on_tap=None, **kwargs):
        super().__init__(**kwargs)
        self.on_tap = on_tap
        self._tap_candidate = False

    def on_touch_down(self, touch):
        if self.disabled or not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if self.readonly and self.on_tap is not None:
            touch.grab(self)
            self._tap_candidate = True
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            if abs(touch.x - touch.ox) > dp(10) or abs(touch.y - touch.oy) > dp(10):
                self._tap_candidate = False
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            should_open = self._tap_candidate
            self._tap_candidate = False
            if should_open and self.on_tap is not None:
                Clock.schedule_once(lambda *_: self.on_tap(), 0)
            return True
        return super().on_touch_up(touch)


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

        self.date_enabled = bool(task and task.due_date)
        self.time_enabled = bool(task and task.due_date and task.due_time)
        self._syncing_switches = False

        self.add_widget(self._build_content())

        if task:
            self._fill_data(task)
        self._sync_deadline_controls()

    def _build_content(self):
        from ui.components import SURFACE_FILL, SURFACE_BORDER
        root = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(16), dp(18), dp(16), dp(16)),
            fill_color=SURFACE_FILL,
            border_color=SURFACE_BORDER,
            radius=dp(30),
        )

        header = Label(
            text=self.form_title,
            color=TEXT_PRIMARY,
            font_size=FONT_SIZE,
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

        self.title_input = GlassTextInput(
            multiline=False,
            hint_text="Введите название задачи",
            input_type="text",
            keyboard_suggestions=True,
        )
        self.description_input = GlassTextInput(
            multiline=True,
            height=dp(120),
            hint_text="Краткое описание или комментарий",
            input_type="text",
            keyboard_suggestions=True,
        )
        category_values = tuple(category.capitalize() for category in CATEGORIES)
        self.category_spinner = GlassSpinner(text=category_values[0], values=category_values)
        recurrence_values = tuple(value.capitalize() for value in RECURRENCE_OPTIONS)
        priority_values = tuple(value.capitalize() for value in PRIORITY_OPTIONS)
        self.recurrence_spinner = GlassSpinner(text=recurrence_values[0], values=recurrence_values)
        self.priority_spinner = GlassSpinner(text=priority_values[1], values=priority_values)

        self.due_date_input = PickerTextInput(
            multiline=False,
            hint_text="Нажмите, чтобы выбрать дату",
            readonly=True,
            on_tap=self._open_date_picker_from_input,
        )
        self.due_date_input.bind(focus=self._on_due_date_focus)
        self.date_toggle = IOSSwitch(
            active=self.date_enabled,
        )
        self.date_toggle.bind(active=self._on_date_toggle)

        self.due_time_input = PickerTextInput(
            multiline=False,
            hint_text="Нажмите, чтобы выбрать время",
            readonly=True,
            on_tap=self._open_time_picker_from_input,
        )
        self.due_time_input.bind(focus=self._on_due_time_focus)
        self.time_toggle = IOSSwitch(
            active=self.time_enabled,
        )
        self.time_toggle.bind(active=self._on_time_toggle)

        form.add_widget(self._build_field("Название", self.title_input))
        form.add_widget(self._build_field("Описание", self.description_input))
        form.add_widget(self._build_field("Категория", self.category_spinner))
        form.add_widget(self._build_deadline_section())
        form.add_widget(self._build_field("Периодичность", self.recurrence_spinner))
        form.add_widget(self._build_field("Приоритет", self.priority_spinner))

        self.message_label = Label(
            text="",
            color=(0.9, 0.32, 0.39, 1),
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
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
            font_size=FONT_SIZE,
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(22), extra=dp(4))

        container.add_widget(title)
        container.add_widget(widget)
        container.bind(minimum_height=container.setter("height"))
        return container

    def _build_deadline_section(self):
        container = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self.date_field_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.date_field_container.bind(minimum_height=self.date_field_container.setter("height"))
        self.date_field_container.add_widget(self._build_toggle_row("Дата", self.date_toggle))
        self.date_field_container.add_widget(self.due_date_input)

        self.time_field_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        self.time_field_container.bind(minimum_height=self.time_field_container.setter("height"))
        self.time_field_container.add_widget(self._build_toggle_row("Время", self.time_toggle))
        self.time_field_container.add_widget(self.due_time_input)

        container.add_widget(self.date_field_container)
        container.add_widget(self.time_field_container)
        container.bind(minimum_height=container.setter("height"))
        return container

    @staticmethod
    def _build_toggle_row(label_text, toggle):
        row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        label = Label(
            text=label_text,
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
        )
        bind_text_size(label)
        row.add_widget(label)
        row.add_widget(toggle)
        return row

    def _fill_data(self, task):
        self.title_input.text = task.title
        self.description_input.text = task.description
        self.category_spinner.text = task.category.capitalize()
        self.due_date_input.text = task.due_date
        self.due_time_input.text = task.due_time
        self.recurrence_spinner.text = task.recurrence.capitalize()
        self.priority_spinner.text = task.priority.capitalize()

    def _handle_save(self):
        due_date = self.due_date_input.text.strip() if self.date_enabled else ""
        due_time = self.due_time_input.text.strip() if self.date_enabled and self.time_enabled else ""

        task_data = {
            "title": self.title_input.text,
            "description": self.description_input.text,
            "category": self.category_spinner.text,
            "due_date": due_date,
            "due_time": due_time,
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

    def toggle_date(self, active=None, open_picker=True):
        self.date_enabled = self.date_enabled if active is None else active
        if not self.date_enabled:
            self.due_date_input.text = ""
            self.time_enabled = False
            self.due_time_input.text = ""
        self._sync_deadline_controls()
        if self.date_enabled and not self.due_date_input.text and open_picker:
            self.open_calendar(allow_disable_on_cancel=True)

    def toggle_time(self, active=None, open_picker=True):
        next_value = self.time_enabled if active is None else active
        if next_value and not self.date_enabled:
            self._sync_deadline_controls()
            return
        self.time_enabled = next_value and self.date_enabled
        if not self.time_enabled:
            self.due_time_input.text = ""
        self._sync_deadline_controls()
        if self.time_enabled and not self.due_time_input.text and open_picker:
            self.open_time_picker(allow_disable_on_cancel=True)

    def _sync_deadline_controls(self):
        self._syncing_switches = True
        self.date_toggle.active = self.date_enabled
        self.time_toggle.active = self.time_enabled
        self._syncing_switches = False
        self.due_date_input.disabled = not self.date_enabled
        self.due_time_input.disabled = not self.time_enabled
        self.time_toggle.disabled = not self.date_enabled

        if self.date_enabled:
            self.due_date_input.hint_text = "Нажмите, чтобы выбрать дату"
        else:
            self.due_date_input.hint_text = "Без даты"

        if self.date_enabled and self.time_enabled:
            self.due_time_input.hint_text = "Нажмите, чтобы выбрать время"
        elif self.date_enabled:
            self.due_time_input.hint_text = "Без времени"
        else:
            self.due_time_input.hint_text = "Сначала включите дату"

        self._sync_optional_field(self.date_field_container, self.due_date_input, self.date_enabled)
        self._sync_optional_field(self.time_field_container, self.due_time_input, self.time_enabled)

    @staticmethod
    def _sync_optional_field(container, widget, enabled):
        if enabled:
            if widget.parent is None:
                container.add_widget(widget)
        elif widget.parent is container:
            container.remove_widget(widget)

    def _on_date_toggle(self, _, active):
        if self._syncing_switches:
            return
        self.toggle_date(active)

    def _on_time_toggle(self, _, active):
        if self._syncing_switches:
            return
        self.toggle_time(active)

    def _on_due_date_focus(self, _, value):
        if value and self.date_enabled:
            Clock.schedule_once(lambda *_: self._open_date_picker_from_input(), 0)

    def _on_due_time_focus(self, _, value):
        if value and self.date_enabled and self.time_enabled:
            Clock.schedule_once(lambda *_: self._open_time_picker_from_input(), 0)

    def _open_date_picker_from_input(self):
        self.due_date_input.focus = False
        self.open_calendar()

    def _open_time_picker_from_input(self):
        self.due_time_input.focus = False
        self.open_time_picker()

    def open_calendar(self, allow_disable_on_cancel=False):
        selected_date = self.due_date_input.text.strip() or date_cls.today().isoformat()
        on_cancel = self._cancel_date_selection if allow_disable_on_cancel else None
        if open_date_picker(selected_date, on_select=self.set_due_date, on_cancel=on_cancel):
            return
        popup = CalendarPickerModal(
            initial_date=selected_date,
            on_select=self.set_due_date,
            on_cancel=on_cancel,
        )
        popup.open()

    def open_time_picker(self, allow_disable_on_cancel=False):
        on_cancel = self._cancel_time_selection if allow_disable_on_cancel else None
        if open_time_picker(self.due_time_input.text.strip(), on_select=self.set_due_time, on_cancel=on_cancel):
            return
        popup = TimePickerModal(
            initial_time=self.due_time_input.text.strip(),
            on_select=self.set_due_time,
            on_cancel=on_cancel,
        )
        popup.open()

    def set_due_date(self, value):
        self.date_enabled = True
        self.due_date_input.text = value
        self._sync_deadline_controls()

    def set_due_time(self, value):
        self.time_enabled = bool(value)
        self.due_time_input.text = value
        self._sync_deadline_controls()

    def _cancel_date_selection(self):
        if not self.due_date_input.text.strip():
            self.toggle_date(False, open_picker=False)

    def _cancel_time_selection(self):
        if not self.due_time_input.text.strip():
            self.toggle_time(False, open_picker=False)


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

    def __init__(self, initial_date: str, on_select, on_cancel=None, **kwargs):
        kwargs.setdefault("size_hint", (0.9, None))
        kwargs.setdefault("height", dp(520))
        kwargs.setdefault("auto_dismiss", True)
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        super().__init__(**kwargs)

        self.overlay_color = (0.1, 0.13, 0.2, 0.24)
        self.on_select = on_select
        self.on_cancel = on_cancel
        self.current_date = date_cls.fromisoformat(initial_date)
        self.display_year = self.current_date.year
        self.display_month = self.current_date.month

        self.content_box = self._build_content()
        self.add_widget(self.content_box)
        self.refresh_days()

    def _build_content(self):
        from ui.components import SURFACE_FILL, SURFACE_BORDER
        root = GlassPane(
            orientation="vertical",
            spacing=dp(12),
            padding=(dp(16), dp(18), dp(16), dp(16)),
            fill_color=SURFACE_FILL,
            border_color=SURFACE_BORDER,
            radius=dp(30),
        )

        title = Label(
            text="Выбор даты",
            color=TEXT_PRIMARY,
            font_size=FONT_SIZE,
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
            font_size=FONT_SIZE,
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
                font_size=FONT_SIZE,
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
        cancel_button.bind(on_release=lambda *_: self.cancel())

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
                    row.add_widget(Label(text="", font_size=FONT_SIZE))
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

    def cancel(self):
        if self.on_cancel is not None:
            self.on_cancel()
        self.dismiss()

    def _sync_year_values(self):
        self.year_spinner.values = tuple(
            str(year) for year in range(self.display_year - 10, self.display_year + 11)
        )


class TimePickerModal(ModalView):
    """Time picker with fixed 24-hour hours and minutes."""

    def __init__(self, initial_time: str, on_select, on_cancel=None, **kwargs):
        kwargs.setdefault("size_hint", (0.84, None))
        kwargs.setdefault("height", dp(280))
        kwargs.setdefault("auto_dismiss", True)
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        super().__init__(**kwargs)

        self.overlay_color = (0.1, 0.13, 0.2, 0.24)
        self.on_select = on_select
        self.on_cancel = on_cancel

        hour, minute = self._split_time(initial_time)
        self.hour_spinner = None
        self.minute_spinner = None
        self.add_widget(self._build_content(hour, minute))

    @staticmethod
    def _split_time(value):
        if value and ":" in value:
            hour, minute = value.split(":", 1)
            if hour.isdigit() and minute.isdigit():
                return f"{int(hour):02d}", f"{int(minute):02d}"
        return "23", "59"

    def _build_content(self, hour, minute):
        from ui.components import SURFACE_FILL, SURFACE_BORDER
        root = GlassPane(
            orientation="vertical",
            spacing=dp(14),
            padding=(dp(16), dp(18), dp(16), dp(16)),
            fill_color=SURFACE_FILL,
            border_color=SURFACE_BORDER,
            radius=dp(30),
        )

        title = Label(
            text="Выбор времени",
            color=TEXT_PRIMARY,
            font_size=FONT_SIZE,
            bold=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(30), extra=dp(4))
        root.add_widget(title)

        picker_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.hour_spinner = GlassSpinner(
            text=hour,
            values=tuple(f"{value:02d}" for value in range(24)),
        )
        colon = Label(
            text=":",
            color=TEXT_PRIMARY,
            size_hint_x=None,
            width=dp(18),
            font_size=FONT_SIZE,
            bold=True,
            halign="center",
            valign="middle",
        )
        bind_text_size(colon)
        self.minute_spinner = GlassSpinner(
            text=minute,
            values=tuple(f"{value:02d}" for value in range(60)),
        )

        picker_row.add_widget(self.hour_spinner)
        picker_row.add_widget(colon)
        picker_row.add_widget(self.minute_spinner)
        root.add_widget(picker_row)

        note = Label(
            text="Только 24-часовой формат: часы 00-23, минуты 00-59.",
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
        )
        bind_text_size(note)
        bind_auto_height(note, min_height=dp(32))
        root.add_widget(note)

        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        cancel_button = GlassButton(text="Отмена", height=dp(46))
        cancel_button.bind(on_release=lambda *_: self.cancel())

        save_button = PrimaryGlassButton(text="Сохранить", height=dp(46))
        save_button.bind(on_release=lambda *_: self.save_time())

        buttons.add_widget(cancel_button)
        buttons.add_widget(save_button)
        root.add_widget(buttons)
        return root

    def save_time(self):
        self.on_select(f"{self.hour_spinner.text}:{self.minute_spinner.text}")
        self.dismiss()

    def cancel(self):
        if self.on_cancel is not None:
            self.on_cancel()
        self.dismiss()
