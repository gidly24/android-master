from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from models import CATEGORIES
from ui.components import (
    BadgeLabel,
    CARD_ACTIVE_BORDER,
    CARD_ACTIVE_FILL,
    CARD_DONE_BORDER,
    CARD_DONE_FILL,
    CARD_OVERDUE_BORDER,
    CARD_OVERDUE_FILL,
    DangerGlassButton,
    GlassButton,
    GlassPane,
    GlassSpinner,
    GlassTextInput,
    PrimaryGlassButton,
    SectionTitle,
    SuccessGlassButton,
    TEXT_MUTED,
    TEXT_PRIMARY,
    bind_auto_height,
    bind_text_size,
)
from ui.forms import TaskFormPopup


class TaskRow(GlassPane):
    """Card widget for a single task."""

    def __init__(self, task, on_edit, on_delete, on_complete, **kwargs):
        fill_color, border_color = self._status_palette(task.status)
        super().__init__(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(14),
            size_hint_y=None,
            fill_color=fill_color,
            border_color=border_color,
            **kwargs,
        )
        self.bind(minimum_height=self.setter("height"))

        title = Label(
            text=task.title,
            color=TEXT_PRIMARY,
            font_size="17sp",
            bold=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(26))
        self.add_widget(title)

        badges = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        badges.add_widget(
            BadgeLabel(
                text=task.category,
                fill_color=(0.16, 0.23, 0.35, 1),
                border_color=(0.34, 0.47, 0.7, 0.95),
            )
        )
        badges.add_widget(self._build_status_badge(task.status))
        badges.add_widget(Widget())
        self.add_widget(badges)

        details = Label(
            text=(
                f"Дата: {task.due_date}\n"
                f"Периодичность: {task.recurrence}\n"
                f"Приоритет: {task.priority}"
            ),
            color=(0.87, 0.9, 0.97, 1),
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        bind_text_size(details)
        bind_auto_height(details, min_height=dp(60))
        self.add_widget(details)

        description = task.description or "Описание не указано."
        description_label = Label(
            text=f"Описание: {description}",
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="top",
        )
        bind_text_size(description_label)
        bind_auto_height(description_label, min_height=dp(28))
        self.add_widget(description_label)

        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))

        edit_button = GlassButton(text="Изменить")
        edit_button.bind(on_release=lambda *_: on_edit(task.id))

        complete_button = SuccessGlassButton(text="Выполнено")
        complete_button.bind(on_release=lambda *_: on_complete(task.id))

        delete_button = DangerGlassButton(text="Удалить")
        delete_button.bind(on_release=lambda *_: on_delete(task.id))

        buttons.add_widget(edit_button)
        buttons.add_widget(complete_button)
        buttons.add_widget(delete_button)
        self.add_widget(buttons)

    @staticmethod
    def _status_palette(status):
        mapping = {
            "активна": (CARD_ACTIVE_FILL, CARD_ACTIVE_BORDER),
            "выполнена": (CARD_DONE_FILL, CARD_DONE_BORDER),
            "просрочена": (CARD_OVERDUE_FILL, CARD_OVERDUE_BORDER),
        }
        return mapping.get(status, (CARD_ACTIVE_FILL, CARD_ACTIVE_BORDER))

    @staticmethod
    def _build_status_badge(status):
        styles = {
            "активна": ((0.18, 0.33, 0.69, 1), (0.46, 0.66, 1, 0.95)),
            "выполнена": ((0.11, 0.45, 0.33, 1), (0.4, 0.83, 0.64, 0.95)),
            "просрочена": ((0.55, 0.2, 0.25, 1), (0.94, 0.55, 0.61, 0.95)),
        }
        fill_color, border_color = styles.get(status, styles["активна"])
        return BadgeLabel(text=status.capitalize(), fill_color=fill_color, border_color=border_color)


class TaskListScreen(Screen):
    """Main screen with filters and task list."""

    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self._build_ui()
        self.refresh_tasks()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(12))
        root.add_widget(self._build_filters())
        root.add_widget(self._build_task_list())
        root.add_widget(self._build_footer())
        self.add_widget(root)

    def _build_filters(self):
        container = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(14), dp(16), dp(14), dp(14)),
            size_hint_y=None,
            height=dp(214),
        )
        container.add_widget(SectionTitle(text="Поиск и фильтрация"))

        self.search_input = GlassTextInput(
            hint_text="Поиск по названию",
            multiline=False,
            height=dp(50),
        )

        filter_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        self.status_spinner = GlassSpinner(
            text="все",
            values=("все", "активна", "просрочена", "выполнена"),
        )
        self.category_spinner = GlassSpinner(
            text="все",
            values=tuple(["все"] + CATEGORIES),
        )

        filter_row.add_widget(self.status_spinner)
        filter_row.add_widget(self.category_spinner)

        button_row = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        apply_button = PrimaryGlassButton(text="Применить")
        apply_button.bind(on_release=lambda *_: self.refresh_tasks())

        reset_button = GlassButton(text="Сбросить")
        reset_button.bind(on_release=lambda *_: self.reset_filters())

        button_row.add_widget(apply_button)
        button_row.add_widget(reset_button)

        container.add_widget(self.search_input)
        container.add_widget(filter_row)
        container.add_widget(button_row)
        return container

    def _build_task_list(self):
        container = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(14), dp(16), dp(14), dp(14)),
        )
        container.add_widget(SectionTitle(text="Список задач"))

        self.scroll_view = ScrollView()
        self.task_box = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self.task_box.bind(minimum_height=self.task_box.setter("height"))
        self.scroll_view.add_widget(self.task_box)
        container.add_widget(self.scroll_view)
        return container

    def _build_footer(self):
        footer = BoxLayout(size_hint_y=None, height=dp(58))
        add_button = PrimaryGlassButton(
            text="Добавить задачу",
            height=dp(54),
            font_size="16sp",
            radius=dp(27),
        )
        add_button.bind(on_release=lambda *_: self.open_task_form())
        footer.add_widget(add_button)
        return footer

    def refresh_tasks(self):
        self.task_box.clear_widgets()
        tasks = self.service.get_tasks(
            status_filter=self.status_spinner.text,
            category_filter=self.category_spinner.text,
            search_text=self.search_input.text.strip(),
        )

        if not tasks:
            empty_label = Label(
                text="Задачи не найдены. Измени фильтр или добавь новую задачу.",
                color=TEXT_MUTED,
                size_hint_y=None,
                halign="center",
                valign="middle",
            )
            bind_text_size(empty_label)
            bind_auto_height(empty_label, min_height=dp(60))
            self.task_box.add_widget(empty_label)
            return

        for task in tasks:
            self.task_box.add_widget(
                TaskRow(
                    task=task,
                    on_edit=self.open_task_form,
                    on_delete=self.confirm_delete,
                    on_complete=self.complete_task,
                )
            )

        self.task_box.add_widget(Widget(size_hint_y=None, height=dp(8)))

    def reset_filters(self):
        self.search_input.text = ""
        self.status_spinner.text = "все"
        self.category_spinner.text = "все"
        self.refresh_tasks()

    def open_task_form(self, task_id=None):
        task = self.service.get_task(task_id) if task_id else None
        popup = TaskFormPopup(on_save=self.save_task, task=task)
        popup.open()

    def save_task(self, task_data, task_id=None):
        self.service.save_task(task_data, task_id)
        self.refresh_tasks()

    def complete_task(self, task_id):
        self.service.mark_task_done(task_id)
        self.refresh_tasks()

    def confirm_delete(self, task_id):
        popup = Popup(
            title="Удаление задачи",
            size_hint=(0.82, 0.32),
            separator_height=1,
            separator_color=(0.31, 0.39, 0.58, 1),
            title_color=TEXT_PRIMARY,
            background_color=(0.05, 0.07, 0.11, 1),
        )
        content = GlassPane(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(14),
            fill_color=(0.08, 0.11, 0.18, 1),
            border_color=(0.29, 0.37, 0.55, 1),
        )

        message = Label(
            text="Удалить задачу без возможности восстановления?",
            color=TEXT_PRIMARY,
            size_hint_y=None,
            halign="center",
            valign="middle",
        )
        bind_text_size(message)
        bind_auto_height(message, min_height=dp(54))
        content.add_widget(message)

        buttons = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        cancel_button = GlassButton(text="Отмена")
        cancel_button.bind(on_release=lambda *_: popup.dismiss())

        delete_button = DangerGlassButton(text="Удалить")
        delete_button.bind(on_release=lambda *_: self._delete_and_close(task_id, popup))

        buttons.add_widget(cancel_button)
        buttons.add_widget(delete_button)
        content.add_widget(buttons)
        popup.content = content
        popup.open()

    def _delete_and_close(self, task_id, popup):
        self.service.delete_task(task_id)
        popup.dismiss()
        self.refresh_tasks()


class StatsScreen(Screen):
    """Statistics screen."""

    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.cards = {}
        self._build_ui()
        self.refresh_stats()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(12))
        root.add_widget(SectionTitle(text="Статистика"))

        for title, fill_color, border_color in [
            ("Всего задач", (0.1, 0.13, 0.21, 1), (0.31, 0.43, 0.68, 1)),
            ("Активных", (0.09, 0.15, 0.24, 1), (0.35, 0.53, 0.85, 1)),
            ("Выполненных", (0.08, 0.16, 0.14, 1), (0.29, 0.63, 0.51, 1)),
            ("Просроченных", (0.18, 0.11, 0.14, 1), (0.7, 0.37, 0.44, 1)),
        ]:
            card = GlassPane(
                orientation="vertical",
                spacing=dp(6),
                padding=dp(14),
                size_hint_y=None,
                height=dp(110),
                fill_color=fill_color,
                border_color=border_color,
            )
            title_label = Label(
                text=title,
                color=(0.82, 0.86, 0.95, 1),
                font_size="16sp",
                bold=True,
            )
            value_label = Label(
                text="0",
                color=TEXT_PRIMARY,
                font_size="30sp",
                bold=True,
            )
            card.add_widget(title_label)
            card.add_widget(value_label)
            self.cards[title] = value_label
            root.add_widget(card)

        note = Label(
            text="Статистика автоматически обновляется после добавления, удаления и выполнения задач.",
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(note)
        bind_auto_height(note, min_height=dp(48))
        root.add_widget(note)
        self.add_widget(root)

    def refresh_stats(self):
        stats = self.service.get_statistics()
        for key, value in stats.items():
            self.cards[key].text = str(value)
