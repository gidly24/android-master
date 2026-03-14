from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
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

SUMMARY_CARDS = [
    ("Активные", CARD_ACTIVE_FILL, "активна"),
    ("Просроченные", CARD_OVERDUE_FILL, "просрочена"),
    ("Выполненные", CARD_DONE_FILL, "выполнена"),
]


class TaskRow(GlassPane):
    """Task card shown either as a list row or as a compact tile."""

    def __init__(self, task, on_edit, on_delete, on_complete, compact=False, **kwargs):
        fill_color, border_color = self._status_palette(task.status)
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(14),
            size_hint_y=None,
            fill_color=fill_color,
            border_color=border_color,
            radius=dp(24),
            **kwargs,
        )
        self.task = task
        self.compact = compact
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_complete = on_complete
        self.bind(minimum_height=self.setter("height"))
        self._build_ui()

    def _build_ui(self):
        self.clear_widgets()

        title = Label(
            text=self.task.title,
            color=(1, 1, 1, 1),
            font_size="16sp" if not self.compact else "15sp",
            bold=True,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(24))
        self.add_widget(title)

        badges = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        badges.add_widget(
            BadgeLabel(
                text=self.task.category,
                fill_color=(1, 1, 1, 0.2),
                border_color=(1, 1, 1, 0.28),
                text_color=(1, 1, 1, 1),
            )
        )
        badges.add_widget(self._build_status_badge(self.task.status))
        badges.add_widget(Widget())
        self.add_widget(badges)

        detail_lines = [f"Дата: {self.task.due_date}"]
        if self.compact:
            detail_lines.append(self.task.recurrence)
        else:
            detail_lines.append(f"Периодичность: {self.task.recurrence}")
            detail_lines.append(f"Приоритет: {self.task.priority}")

        details = Label(
            text="\n".join(detail_lines),
            color=(1, 1, 1, 0.96),
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size="13sp",
        )
        bind_text_size(details)
        bind_auto_height(details, min_height=dp(44) if self.compact else dp(62))
        self.add_widget(details)

        if not self.compact:
            description = self.task.description or "Описание не указано."
            description_label = Label(
                text=f"Описание: {description}",
                color=(1, 1, 1, 0.9),
                size_hint_y=None,
                halign="left",
                valign="top",
                font_size="13sp",
            )
            bind_text_size(description_label)
            bind_auto_height(description_label, min_height=dp(26))
            self.add_widget(description_label)

        buttons = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        if self.compact:
            edit_button = GlassButton(text="Изм.", font_size="13sp", height=dp(40))
            complete_button = SuccessGlassButton(text="Готово", font_size="13sp", height=dp(40))
            delete_button = DangerGlassButton(text="Удал.", font_size="13sp", height=dp(40))
        else:
            edit_button = GlassButton(text="Изменить", height=dp(40))
            complete_button = SuccessGlassButton(text="Выполнено", height=dp(40))
            delete_button = DangerGlassButton(text="Удалить", height=dp(40))

        edit_button.bind(on_release=lambda *_: self.on_edit(self.task.id))
        complete_button.bind(on_release=lambda *_: self.on_complete(self.task.id))
        delete_button.bind(on_release=lambda *_: self.on_delete(self.task.id))

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
        return BadgeLabel(
            text=status.capitalize(),
            fill_color=(1, 1, 1, 0.2),
            border_color=(1, 1, 1, 0.28),
            text_color=(1, 1, 1, 1),
        )


class TaskListScreen(Screen):
    """Main screen with summary, filters and task list."""

    def __init__(self, service, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.filters_expanded = False
        self.view_mode = "list"
        self._build_ui()
        self.refresh_tasks()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(12))
        root.add_widget(self._build_summary_cards())
        root.add_widget(self._build_task_list())
        root.add_widget(self._build_footer())
        self.add_widget(root)

    def _build_summary_cards(self):
        container = BoxLayout(size_hint_y=None, height=dp(118), spacing=dp(10))
        self.summary_labels = {}

        for title, color, key in SUMMARY_CARDS:
            card = GlassPane(
                orientation="vertical",
                padding=(dp(12), dp(12), dp(12), dp(10)),
                spacing=dp(2),
                fill_color=color,
                border_color=color,
                radius=dp(24),
            )
            name_label = Label(
                text=title,
                color=(1, 1, 1, 0.96),
                font_size="14sp",
                bold=True,
                size_hint_y=None,
                height=dp(24),
                halign="left",
                valign="middle",
            )
            bind_text_size(name_label)
            value_label = Label(
                text="0",
                color=(1, 1, 1, 1),
                font_size="32sp",
                bold=True,
                halign="right",
                valign="middle",
            )
            card.add_widget(name_label)
            card.add_widget(value_label)
            self.summary_labels[key] = value_label
            container.add_widget(card)

        return container

    @staticmethod
    def _build_panel_header(text, right_widget=None):
        header = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        header.add_widget(SectionTitle(text=text))
        if right_widget is not None:
            header.add_widget(right_widget)
        return header

    def _build_task_list(self):
        container = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(16), dp(18), dp(16), dp(14)),
        )

        controls = BoxLayout(size_hint_x=None, width=dp(164), spacing=dp(8))

        self.filter_toggle_button = GlassButton(
            text="Ф",
            size_hint_x=None,
            width=dp(48),
            height=dp(40),
            radius=dp(20),
            font_size="15sp",
        )
        self.filter_toggle_button.bind(on_release=lambda *_: self.toggle_filters())

        self.view_toggle_button = GlassButton(
            text="Список",
            size_hint_x=None,
            width=dp(108),
            height=dp(40),
            radius=dp(20),
            font_size="13sp",
        )
        self.view_toggle_button.bind(on_release=lambda *_: self.toggle_view_mode())

        controls.add_widget(self.filter_toggle_button)
        controls.add_widget(self.view_toggle_button)

        container.add_widget(self._build_panel_header("Список задач", controls))

        self.filter_host = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=0,
            opacity=0,
        )
        container.add_widget(self.filter_host)

        self.filter_panel = self._build_filters_panel()

        self.scroll_view = ScrollView(bar_width=dp(4), scroll_type=["bars", "content"])
        self.task_container = None
        self._rebuild_task_container()
        container.add_widget(self.scroll_view)

        self._sync_filter_panel()
        self._sync_view_button()
        return container

    def _build_filters_panel(self):
        container = GlassPane(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(12), dp(12), dp(12), dp(12)),
            size_hint_y=None,
            height=dp(178),
            fill_color=(1, 1, 1, 1),
            border_color=(0.85, 0.87, 0.91, 1),
            radius=dp(24),
        )

        self.search_input = GlassTextInput(
            hint_text="Поиск по названию",
            multiline=False,
            height=dp(48),
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
        apply_button.bind(on_release=lambda *_: self.apply_filters())

        reset_button = GlassButton(text="Сбросить")
        reset_button.bind(on_release=lambda *_: self.reset_filters())

        button_row.add_widget(apply_button)
        button_row.add_widget(reset_button)

        container.add_widget(self.search_input)
        container.add_widget(filter_row)
        container.add_widget(button_row)
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

    def _rebuild_task_container(self):
        if self.task_container is not None:
            self.scroll_view.remove_widget(self.task_container)

        if self.view_mode == "tile":
            self.task_container = GridLayout(
                cols=2,
                spacing=dp(10),
                size_hint_y=None,
                padding=(0, 0, 0, dp(4)),
            )
        else:
            self.task_container = BoxLayout(
                orientation="vertical",
                spacing=dp(10),
                size_hint_y=None,
                padding=(0, 0, 0, dp(4)),
            )

        self.task_container.bind(minimum_height=self.task_container.setter("height"))
        self.scroll_view.add_widget(self.task_container)

    def refresh_tasks(self):
        self.task_container.clear_widgets()
        tasks = self.service.get_tasks(
            status_filter=self.status_spinner.text,
            category_filter=self.category_spinner.text,
            search_text=self.search_input.text.strip(),
        )

        self._refresh_summary(tasks)

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
            self.task_container.add_widget(empty_label)
            return

        for task in tasks:
            row = TaskRow(
                task=task,
                on_edit=self.open_task_form,
                on_delete=self.confirm_delete,
                on_complete=self.complete_task,
                compact=self.view_mode == "tile",
            )
            if self.view_mode == "tile":
                row.size_hint_y = None
                row.height = dp(208)
            self.task_container.add_widget(row)

        self.task_container.add_widget(Widget(size_hint_y=None, height=dp(8)))

    def _refresh_summary(self, tasks):
        counts = {
            "активна": len([task for task in tasks if task.status == "активна"]),
            "просрочена": len([task for task in tasks if task.status == "просрочена"]),
            "выполнена": len([task for task in tasks if task.status == "выполнена"]),
        }
        for key, label in self.summary_labels.items():
            label.text = str(counts.get(key, 0))

    def toggle_filters(self):
        self.filters_expanded = not self.filters_expanded
        self._sync_filter_panel()

    def _sync_filter_panel(self):
        if self.filters_expanded:
            if self.filter_panel.parent is None:
                self.filter_host.add_widget(self.filter_panel)
            self.filter_host.height = self.filter_panel.height
            self.filter_host.opacity = 1
            self.filter_toggle_button.text = "X"
            self.filter_toggle_button.set_palette(
                fill_color=(0.91, 0.95, 1, 1),
                border_color=(0.33, 0.66, 0.95, 1),
                text_color=TEXT_PRIMARY,
            )
        else:
            if self.filter_panel.parent is self.filter_host:
                self.filter_host.remove_widget(self.filter_panel)
            self.filter_host.height = 0
            self.filter_host.opacity = 0
            self.filter_toggle_button.text = "Ф"
            self.filter_toggle_button.set_palette(
                fill_color=(1, 1, 1, 0.98),
                border_color=(0.84, 0.87, 0.92, 1),
                text_color=TEXT_PRIMARY,
            )

    def toggle_view_mode(self):
        self.view_mode = "tile" if self.view_mode == "list" else "list"
        self._rebuild_task_container()
        self._sync_view_button()
        self.refresh_tasks()

    def _sync_view_button(self):
        if self.view_mode == "tile":
            self.view_toggle_button.text = "Плитка"
        else:
            self.view_toggle_button.text = "Список"
        self.view_toggle_button.set_palette(
            fill_color=(1, 1, 1, 0.98),
            border_color=(0.84, 0.87, 0.92, 1),
            text_color=TEXT_PRIMARY,
        )

    def apply_filters(self):
        self.refresh_tasks()
        self.filters_expanded = False
        self._sync_filter_panel()

    def reset_filters(self):
        self.search_input.text = ""
        self.status_spinner.text = "все"
        self.category_spinner.text = "все"
        self.refresh_tasks()
        self.filters_expanded = False
        self._sync_filter_panel()

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
        popup = ModalView(
            size_hint=(0.84, None),
            height=dp(230),
            auto_dismiss=True,
            background="",
            background_color=(0, 0, 0, 0),
        )
        popup.overlay_color = (0.1, 0.13, 0.2, 0.24)

        content = GlassPane(
            orientation="vertical",
            spacing=dp(14),
            padding=(dp(16), dp(18), dp(16), dp(16)),
            fill_color=(1, 1, 1, 1),
            border_color=(0.85, 0.87, 0.91, 1),
            radius=dp(30),
        )

        header = Label(
            text="Удаление задачи",
            color=TEXT_PRIMARY,
            size_hint_y=None,
            font_size="20sp",
            bold=True,
            halign="left",
            valign="middle",
        )
        bind_text_size(header)
        bind_auto_height(header, min_height=dp(30), extra=dp(4))
        content.add_widget(header)

        message = Label(
            text="Удалить задачу без возможности восстановления?",
            color=TEXT_PRIMARY,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(message)
        bind_auto_height(message, min_height=dp(50))
        content.add_widget(message)

        note = Label(
            text="Это действие нельзя отменить.",
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
        )
        bind_text_size(note)
        bind_auto_height(note, min_height=dp(24), extra=dp(4))
        content.add_widget(note)

        buttons = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        cancel_button = GlassButton(text="Отмена", height=dp(46))
        cancel_button.bind(on_release=lambda *_: popup.dismiss())

        delete_button = DangerGlassButton(text="Удалить", height=dp(46))
        delete_button.bind(on_release=lambda *_: self._delete_and_close(task_id, popup))

        buttons.add_widget(cancel_button)
        buttons.add_widget(delete_button)
        content.add_widget(buttons)
        popup.add_widget(content)
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
            ("Всего задач", (1, 1, 1, 1), (0.85, 0.87, 0.91, 1)),
            ("Активных", CARD_ACTIVE_FILL, CARD_ACTIVE_BORDER),
            ("Выполненных", CARD_DONE_FILL, CARD_DONE_BORDER),
            ("Просроченных", CARD_OVERDUE_FILL, CARD_OVERDUE_BORDER),
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
                color=TEXT_PRIMARY if title == "Всего задач" else (1, 1, 1, 0.95),
                font_size="16sp",
                bold=True,
            )
            value_label = Label(
                text="0",
                color=TEXT_PRIMARY if title == "Всего задач" else (1, 1, 1, 1),
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
