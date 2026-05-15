from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from models import CATEGORIES
from services import TaskService
from ui.components import (
    APP_BACKGROUND,
    FONT_SIZE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    CARD_ACTIVE_FILL,
    CARD_DONE_FILL,
    CARD_OVERDUE_FILL,
    M3_PRIMARY,
    POPUP_SURFACE,
    TRANSPARENT_APP,
    Chip,
    CircleButton,
    DangerButton,
    FilledButton,
    IconCircleButton,
    MaterialLabel as Label,
    MaterialButton,
    MaterialCard,
    MaterialSpinner,
    MaterialTextInput,
    bind_auto_height,
    bind_text_size,
)
from ui.forms import TaskFormPopup

EDIT_ICON = "assets/icons/edit.ico"
DONE_ICON = "assets/icons/done.ico"
DELETE_ICON = "assets/icons/delete.ico"
MORE_ICON = "assets/icons/more.ico"


class TaskRow(MaterialCard):
    def __init__(self, task, on_edit, on_delete, on_complete, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=(dp(12), dp(9), dp(12), dp(9)),
            size_hint_y=None,
            fill_color=self._fill(task.status),
            **kwargs,
        )
        self.bind(minimum_height=self.setter("height"))
        self.task = task
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_complete = on_complete
        self._build()

    @staticmethod
    def _fill(status):
        return {
            "активна": CARD_ACTIVE_FILL,
            "выполнена": CARD_DONE_FILL,
            "просрочена": CARD_OVERDUE_FILL,
        }.get(status, CARD_ACTIVE_FILL)

    def _build(self):
        row = BoxLayout(size_hint_y=None, spacing=dp(6))
        row.bind(minimum_height=row.setter("height"))
        t = Label(text=self.task.title, color=TEXT_PRIMARY, size_hint_y=None, halign="left", valign="middle", font_size=FONT_SIZE, bold=True)
        bind_text_size(t)
        bind_auto_height(t, min_height=dp(22), extra=dp(2))
        row.add_widget(t)
        row.add_widget(Chip(text=self.task.status.capitalize()))
        self.add_widget(row)

        category = Label(
            text=self.task.category.capitalize(),
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
            bold=True,
        )
        bind_text_size(category)
        bind_auto_height(category, min_height=dp(22), extra=dp(2))
        self.add_widget(category)

        countdown = Label(
            text=TaskService.get_countdown_text(self.task).replace("Осталось: ", "").replace("Просрочена на: ", "Просрочка "),
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
            bold=True,
        )
        bind_text_size(countdown)
        bind_auto_height(countdown, min_height=dp(22), extra=dp(2))
        self.add_widget(countdown)

        description = Label(
            text=self.task.description.strip() if self.task.description else "Без описания.",
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size=FONT_SIZE,
            bold=True,
        )
        bind_text_size(description)
        bind_auto_height(description, min_height=dp(20), extra=dp(2))
        self.add_widget(description)

        action_size = dp(38)
        actions = BoxLayout(size_hint_y=None, height=action_size, spacing=dp(6))
        e = IconCircleButton(
            icon_source=EDIT_ICON,
            fallback_text="И",
            width=action_size,
            height=action_size,
            radius=action_size / 2,
            font_size=FONT_SIZE,
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
        )
        e.bind(on_release=lambda *_: self.on_edit(self.task.id))
        c = IconCircleButton(
            icon_source=DONE_ICON,
            fallback_text="Г",
            width=action_size,
            height=action_size,
            radius=action_size / 2,
            font_size=FONT_SIZE,
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
        )
        c.bind(on_release=lambda *_: self.on_complete(self.task.id))
        d = IconCircleButton(
            icon_source=DELETE_ICON,
            fallback_text="У",
            width=action_size,
            height=action_size,
            radius=action_size / 2,
            font_size=FONT_SIZE,
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
        )
        d.bind(on_release=lambda *_: self.on_delete(self.task.id))
        actions.add_widget(Widget())
        actions.add_widget(e)
        actions.add_widget(c)
        actions.add_widget(d)
        self.add_widget(actions)


class TaskListScreen(Screen):
    def __init__(self, service, on_tasks_changed=None, on_open_chat=None, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.on_tasks_changed = on_tasks_changed
        self.on_open_chat = on_open_chat
        self.filters_visible = False
        self.filters_panel = None
        self.filters_host = None
        self._build_ui()
        self.refresh_tasks()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=(dp(8), dp(8), dp(8), dp(8)))

        top = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8),
            padding=(dp(8), 0, dp(8), 0),
        )

        title = Label(
            text="Задачи",
            color=TEXT_PRIMARY,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
            bold=True,
        )

        title.bind(size=lambda *_: setattr(title, "text_size", title.size))

        self.filter_btn = IconCircleButton(
            icon_source=MORE_ICON,
            fallback_text="⋮",
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            size_hint=(None, None),
            size=(dp(38), dp(38)),
        )

        top.add_widget(title)
        top.add_widget(Widget())
        top.add_widget(self.filter_btn)

        root.add_widget(top)

        self.filters_host = BoxLayout(orientation="vertical", size_hint_y=None, height=0, opacity=0)
        self.filters_panel = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.filters_panel.bind(minimum_height=self.filters_panel.setter("height"))
        input_height = dp(44)
        self.search_input = MaterialTextInput(multiline=False, hint_text="Поиск по названию", size_hint_y=None, height=input_height)
        self.status_spinner = MaterialSpinner(text="Все", values=("Все", "Активна", "Просрочена", "Выполнена"), size_hint_x=1, size_hint_y=None, height=input_height)
        self.category_spinner = MaterialSpinner(text="Все", values=tuple(["Все"] + [c.capitalize() for c in CATEGORIES]), size_hint_x=1, size_hint_y=None, height=input_height)
        sp = BoxLayout(size_hint_y=None, height=input_height, spacing=dp(6))
        sp.add_widget(self.status_spinner)
        sp.add_widget(self.category_spinner)
        fa = BoxLayout(size_hint_y=None, height=input_height, spacing=dp(6))
        apply_btn = FilledButton(text="Применить", height=input_height, size_hint_x=1)
        apply_btn.bind(on_release=lambda *_: self.apply_filters())
        reset_btn = MaterialButton(text="Сброс", height=input_height, size_hint_x=1)
        reset_btn.bind(on_release=lambda *_: self.reset_filters())
        fa.add_widget(apply_btn)
        fa.add_widget(reset_btn)
        self.filters_panel.add_widget(self.search_input)
        self.filters_panel.add_widget(sp)
        self.filters_panel.add_widget(fa)
        root.add_widget(self.filters_host)

        self.scroll = ScrollView()
        self.task_container = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None, padding=(0, 0, 0, dp(4)))
        self.task_container.bind(minimum_height=self.task_container.setter("height"))
        self.scroll.add_widget(self.task_container)
        root.add_widget(self.scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(58), spacing=dp(10), padding=(0, dp(2), 0, 0))
        add_btn = CircleButton(text="+", fill_color=M3_PRIMARY, text_color=TEXT_PRIMARY)
        add_btn.bind(on_release=lambda *_: self.open_task_form())
        chat_btn = IconCircleButton(
            icon_source="assets/icons/chat.ico",
            fallback_text="💬",
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY
        )
        chat_btn.bind(on_release=lambda *_: self._open_chat())
        footer.add_widget(Widget())
        footer.add_widget(add_btn)
        footer.add_widget(chat_btn)
        root.add_widget(footer)
        self.add_widget(root)

    def toggle_filters(self):
        self.filters_visible = not self.filters_visible
        if self.filters_visible:
            if self.filters_panel.parent is None:
                self.filters_host.add_widget(self.filters_panel)
            self.filters_host.opacity = 1
            self.filters_host.height = self.filters_panel.height
        else:
            if self.filters_panel.parent is self.filters_host:
                self.filters_host.remove_widget(self.filters_panel)
            self.filters_host.opacity = 0
            self.filters_host.height = 0

    def apply_filters(self):
        self.refresh_tasks()
        self.filters_visible = False
        if self.filters_panel.parent is self.filters_host:
            self.filters_host.remove_widget(self.filters_panel)
        self.filters_host.opacity = 0
        self.filters_host.height = 0

    def _open_chat(self):
        if self.on_open_chat:
            self.on_open_chat()

    def refresh_tasks(self):
        self.task_container.clear_widgets()
        tasks = self.service.get_tasks(
            status_filter=self.status_spinner.text,
            category_filter=self.category_spinner.text,
            search_text=self.search_input.text.strip(),
        )
        if not tasks:
            empty = Label(text="Задачи не найдены.", color=TEXT_MUTED, size_hint_y=None, halign="center", valign="middle", font_size=FONT_SIZE)
            bind_text_size(empty)
            bind_auto_height(empty, min_height=dp(44), extra=dp(2))
            self.task_container.add_widget(empty)
            return
        for task in tasks:
            self.task_container.add_widget(TaskRow(task=task, on_edit=self.open_task_form, on_delete=self.confirm_delete, on_complete=self.complete_task))

    def reset_filters(self):
        self.search_input.text = ""
        self.status_spinner.text = "Все"
        self.category_spinner.text = "Все"
        self.refresh_tasks()

    def open_task_form(self, task_id=None):
        task = self.service.get_task(task_id) if task_id else None
        TaskFormPopup(on_save=self.save_task, task=task).open()

    def save_task(self, task_data, task_id=None):
        self.service.save_task(task_data, task_id)
        self.refresh_tasks()
        if self.on_tasks_changed:
            self.on_tasks_changed()

    def complete_task(self, task_id):
        self.service.mark_task_done(task_id)
        self.refresh_tasks()
        if self.on_tasks_changed:
            self.on_tasks_changed()

    def confirm_delete(self, task_id):
        popup = ModalView(size_hint=(0.84, None), height=dp(160), auto_dismiss=True, background="", background_color=TRANSPARENT_APP)
        popup.overlay_color = (APP_BACKGROUND[0], APP_BACKGROUND[1], APP_BACKGROUND[2], 0.45)
        card = MaterialCard(orientation="vertical", spacing=dp(8), padding=(dp(12), dp(12), dp(12), dp(10)), fill_color=POPUP_SURFACE)
        text = Label(text="Удалить задачу?", color=TEXT_PRIMARY, size_hint_y=None, halign="left", valign="middle", font_size=FONT_SIZE)
        bind_text_size(text)
        bind_auto_height(text, min_height=dp(34), extra=dp(2))
        card.add_widget(text)
        actions = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        cancel = MaterialButton(text="Отмена", height=dp(38))
        cancel.bind(on_release=lambda *_: popup.dismiss())
        delete = DangerButton(text="Удалить", height=dp(38))
        delete.bind(on_release=lambda *_: self._delete_and_close(task_id, popup))
        actions.add_widget(cancel)
        actions.add_widget(delete)
        card.add_widget(actions)
        popup.add_widget(card)
        popup.open()

    def _delete_and_close(self, task_id, popup):
        self.service.delete_task(task_id)
        popup.dismiss()
        self.refresh_tasks()
        if self.on_tasks_changed:
            self.on_tasks_changed()


class ArchiveScreen(Screen):
    def __init__(self, service, on_clear_all=None, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.on_clear_all = on_clear_all
        self._build_ui()
        self.refresh_archive()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=(dp(8), dp(8), dp(8), dp(8)))
        title = Label(text="Архив", color=TEXT_PRIMARY, font_size=FONT_SIZE, bold=True, size_hint_y=None, halign="left", valign="middle")
        bind_text_size(title)
        bind_auto_height(title, min_height=dp(28), extra=dp(2))
        root.add_widget(title)
        self.search_input = MaterialTextInput(multiline=False, hint_text="Поиск по архиву")
        root.add_widget(self.search_input)
        actions = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        r = FilledButton(text="Обновить", height=dp(38))
        r.bind(on_release=lambda *_: self.refresh_archive())
        c = DangerButton(text="Очистить архив", height=dp(38))
        c.bind(on_release=lambda *_: self._clear_all_archive())
        actions.add_widget(r)
        actions.add_widget(c)
        root.add_widget(actions)
        self.scroll = ScrollView()
        self.archive_box = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_y=None)
        self.archive_box.bind(minimum_height=self.archive_box.setter("height"))
        self.scroll.add_widget(self.archive_box)
        root.add_widget(self.scroll)
        self.add_widget(root)

    def refresh_archive(self):
        self.archive_box.clear_widgets()
        tasks = self.service.get_archived_tasks(self.search_input.text.strip())
        if not tasks:
            empty = Label(text="Архив пуст.", color=TEXT_MUTED, size_hint_y=None, halign="center", valign="middle", font_size=FONT_SIZE)
            bind_text_size(empty)
            bind_auto_height(empty, min_height=dp(40), extra=dp(2))
            self.archive_box.add_widget(empty)
            return
        for task in tasks:
            row = MaterialCard(orientation="vertical", spacing=dp(5), padding=(dp(10), dp(8), dp(10), dp(8)), size_hint_y=None, fill_color=POPUP_SURFACE)
            row.bind(minimum_height=row.setter("height"))
            t = Label(text=task.title, color=TEXT_PRIMARY, bold=True, size_hint_y=None, halign="left", valign="middle", font_size=FONT_SIZE)
            bind_text_size(t)
            bind_auto_height(t, min_height=dp(20), extra=dp(2))
            m = Label(text=f"Категория: {task.category.capitalize()} | {task.archived_at or 'Недавно'}", color=TEXT_MUTED, size_hint_y=None, halign="left", valign="middle", font_size=FONT_SIZE)
            bind_text_size(m)
            bind_auto_height(m, min_height=dp(20), extra=dp(2))
            d = DangerButton(text="Удалить", height=dp(34))
            d.bind(on_release=lambda *_, task_id=task.id: self._delete_archived(task_id))
            row.add_widget(t)
            row.add_widget(m)
            row.add_widget(d)
            self.archive_box.add_widget(row)

    def _delete_archived(self, task_id):
        self.service.delete_task(task_id)
        self.refresh_archive()

    def _clear_all_archive(self):
        if self.on_clear_all:
            self.on_clear_all()
        else:
            self.service.clear_archived_tasks()
            self.refresh_archive()
