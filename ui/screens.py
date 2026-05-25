from kivy.graphics import Color, Ellipse
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.uix.relativelayout import RelativeLayout
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
    M3_OUTLINE,
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

EDIT_ICON = "assets/icons/edit.png"
DONE_ICON = "assets/icons/done.png"
DELETE_ICON = "assets/icons/delete.png"
MORE_ICON = "assets/icons/more.png"
RESTORE_ICON = "assets/icons/restore.png"
CHAT_ICON = "assets/icons/chat.png"


class SelectionToggle(Widget):
    def __init__(self, is_selected=False, **kwargs):
        super().__init__(size_hint=(None, None), size=(dp(34), dp(34)), **kwargs)
        self.is_selected = is_selected
        with self.canvas.before:
            self._color = Color()
            self._bg = Ellipse(pos=self.pos, size=self.size)
            self._inner_color = Color(*APP_BACKGROUND)
            self._inner = Ellipse(
                pos=(self.x + dp(2), self.y + dp(2)), 
                size=(dp(30), dp(30))
            )
        self.bind(pos=self._update_canvas, size=self._update_canvas)
        self._update_canvas()

    def _update_canvas(self, *_):
        if self.is_selected:
            self._color.rgba = M3_PRIMARY
            self._inner_color.rgba = M3_PRIMARY
        else:
            self._color.rgba = TEXT_MUTED
            self._inner_color.rgba = APP_BACKGROUND

        self._bg.pos = self.pos
        self._bg.size = self.size
        self._inner.pos = (self.x + dp(2), self.y + dp(2))
        self._inner.size = (dp(30), dp(30))


class TaskRow(MaterialCard):
    def __init__(self, task, on_edit, on_delete, on_complete, on_select=None, is_selected=False, is_archive=False, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(8),
            padding=(dp(12), dp(9), dp(12), dp(9)),
            size_hint_y=None,
            fill_color=self._fill(task.status) if not is_selected else POPUP_SURFACE,
            border_color=M3_PRIMARY if is_selected else M3_OUTLINE,
            radius=dp(16),
            **kwargs,
        )
        self.bind(minimum_height=self.setter("height"))
        self.task = task
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_complete = on_complete
        self.on_select = on_select
        self.is_selected = is_selected
        self.is_archive = is_archive
        self._build()

    @staticmethod
    def _fill(status):
        return {
            "активна": CARD_ACTIVE_FILL,
            "выполнена": CARD_DONE_FILL,
            "просрочена": CARD_OVERDUE_FILL,
        }.get(status, CARD_ACTIVE_FILL)

    def _build(self):
        card_content_layout = BoxLayout(orientation='vertical', spacing=dp(5), padding=(0, dp(4), 0, 0), size_hint_y=None)
        card_content_layout.bind(minimum_height=card_content_layout.setter('height'))

        top_row = BoxLayout(orientation='horizontal', size_hint_y=None, spacing=dp(10), height=dp(34))

        self.selector = SelectionToggle(is_selected=self.is_selected)
        selector_btn = Button(
            size_hint=(None, None), 
            size=(dp(34), dp(34)),
            background_color=(0,0,0,0)
        )
        selector_btn.add_widget(self.selector)
        self.selector.pos = (selector_btn.x + dp(5), selector_btn.y + dp(5))
        selector_btn.bind(pos=lambda *_: setattr(self.selector, 'pos', (selector_btn.x + dp(5), selector_btn.y + dp(5))))
        
        if self.on_select:
            selector_btn.bind(on_release=lambda *_: self.on_select(self.task.id))
        
        top_row.add_widget(selector_btn)

        t = Label(text=self.task.title, color=TEXT_PRIMARY, size_hint_y=None, halign="left", valign="middle", font_size=FONT_SIZE, bold=True)
        bind_text_size(t)
        bind_auto_height(t, min_height=dp(22), extra=dp(2))
        top_row.add_widget(t)

        top_row.add_widget(Widget(size_hint_x=1))
        
        status_chip = Chip(text=self.task.status.capitalize())
        top_row.add_widget(status_chip)
        
        card_content_layout.add_widget(top_row)

        category = Label(
            text=self.task.category.capitalize(),
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
            bold=True
        )
        bind_text_size(category)
        bind_auto_height(category, min_height=dp(22), extra=dp(2))
        card_content_layout.add_widget(category)

        countdown = Label(
            text=TaskService.get_countdown_text(self.task).replace("Осталось: ", "").replace("Просрочена на: ", "Просрочка "),
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=FONT_SIZE,
            bold=True
        )
        bind_text_size(countdown)
        bind_auto_height(countdown, min_height=dp(22), extra=dp(2))
        card_content_layout.add_widget(countdown)

        description = Label(
            text=self.task.description.strip() if self.task.description else "Без описания.",
            color=TEXT_MUTED,
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size=FONT_SIZE,
            bold=True
        )
        bind_text_size(description)
        bind_auto_height(description, min_height=dp(20), extra=dp(2))
        card_content_layout.add_widget(description)

        action_size = dp(38)
        actions = BoxLayout(size_hint_y=None, height=action_size, spacing=dp(6))
        
        if not self.is_archive:
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
            actions.add_widget(e)

        c = IconCircleButton(
            icon_source=RESTORE_ICON if self.is_archive else DONE_ICON,
            fallback_text="В" if self.is_archive else "Г",
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
        actions.add_widget(c)
        actions.add_widget(d)

        self.add_widget(card_content_layout)
        self.add_widget(actions)


class TaskListScreen(Screen):
    def __init__(self, service, on_tasks_changed, on_open_chat, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.on_tasks_changed = on_tasks_changed
        self.on_open_chat = on_open_chat
        self.selected_task_ids = set()
        self.status_filter = "активные"
        self.category_filter = "все"
        self.search_text = ""

        self.root_layout = RelativeLayout()
        self.main_container = BoxLayout(orientation='vertical', padding=dp(0), spacing=dp(0))

        # --- Header ---
        header = BoxLayout(size_hint_y=None, height=dp(56), padding=(dp(16), 0, dp(16), 0))
        header.add_widget(Label(
            text="Мои задачи", 
            font_size=FONT_SIZE, 
            bold=True, 
            halign="left", 
            valign="middle",
            size_hint_x=None,
            width=dp(150)
        ))
        header.add_widget(Widget())
        self.main_container.add_widget(header)

        # --- Search Bar ---
        search_bar = BoxLayout(size_hint_y=None, height=dp(48), padding=(dp(16), dp(4)), spacing=dp(8))
        self.search_input = MaterialTextInput(hint_text="Поиск задач...", multiline=False, height=dp(40))
        self.search_input.bind(text=self.on_search_change)
        search_bar.add_widget(self.search_input)
        self.main_container.add_widget(search_bar)

        # --- Embedded Filters ---
        filters_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4), padding=(dp(16), dp(4), dp(16), dp(8)))
        
        status_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        status_row.add_widget(Label(text="Статус:", font_size=FONT_SIZE, bold=True, size_hint_x=None, width=dp(100), halign="left"))
        self.status_spinner = MaterialSpinner(
            text=self.status_filter.capitalize(),
            values=("Все", "Активные", "Выполненные", "Просроченные"),
            height=dp(36),
            radius=dp(18)
        )
        self.status_spinner.bind(text=self.on_filter_change)
        status_row.add_widget(self.status_spinner)
        filters_box.add_widget(status_row)

        cat_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cat_row.add_widget(Label(text="Категория:", font_size=FONT_SIZE, bold=True, size_hint_x=None, width=dp(100), halign="left"))
        cat_values = ["Все"] + [c.capitalize() for c in CATEGORIES]
        self.category_spinner = MaterialSpinner(
            text=self.category_filter.capitalize(),
            values=tuple(cat_values),
            height=dp(36),
            radius=dp(18)
        )
        self.category_spinner.bind(text=self.on_filter_change)
        cat_row.add_widget(self.category_spinner)
        filters_box.add_widget(cat_row)

        filters_box.height = dp(88)
        self.main_container.add_widget(filters_box)

        self.scroll = ScrollView(do_scroll_x=False)
        self.task_list_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, padding=dp(10))
        self.task_list_layout.bind(minimum_height=self.task_list_layout.setter('height'))
        self.scroll.add_widget(self.task_list_layout)
        self.main_container.add_widget(self.scroll)

        # --- Batch Actions ---
        self.batch_actions = MaterialCard(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            opacity=0,
            padding=(dp(16), dp(8), dp(16), dp(8)),
            spacing=dp(12),
            fill_color=POPUP_SURFACE,
            radius=0
        )
        btn_complete = FilledButton(text="Выполнить", size_hint_x=1, height=dp(40), font_size=FONT_SIZE, bold=True)
        btn_complete.bind(on_release=self.complete_selected)
        btn_delete = DangerButton(text="Удалить", size_hint_x=1, height=dp(40), font_size=FONT_SIZE, bold=True)
        btn_delete.bind(on_release=self.delete_selected)
        self.batch_actions.add_widget(btn_complete)
        self.batch_actions.add_widget(btn_delete)
        self.main_container.add_widget(self.batch_actions)

        self.root_layout.add_widget(self.main_container)

        # --- FABs Group ---
        fabs = BoxLayout(orientation='horizontal', size_hint=(None, None), size=(dp(124), dp(56)), spacing=dp(12), pos_hint={'right': 0.95, 'top': 0.12})

        # screens.py
        self.chat_fab = IconCircleButton(  # <--- Меняем на IconCircleButton
            icon_source=CHAT_ICON,
            fallback_text="Ч",
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            font_size="24sp"
        )
        self.chat_fab.bind(on_release=lambda *_: self.on_open_chat())
        
        self.add_fab = CircleButton(
            text="+",
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            font_size="32sp"
        )
        self.add_fab.bind(on_release=lambda *_: self.add_task())
        
        fabs.add_widget(self.chat_fab)
        fabs.add_widget(self.add_fab)
        self.root_layout.add_widget(fabs)

        self.add_widget(self.root_layout)
        self.refresh_tasks()

    def on_search_change(self, instance, value):
        self.search_text = value
        self.refresh_tasks()

    def on_filter_change(self, instance, value):
        self.status_filter = self.status_spinner.text.lower()
        self.category_filter = self.category_spinner.text.lower()
        self.refresh_tasks()

    def refresh_tasks(self):
        self.task_list_layout.clear_widgets()
        tasks = self.service.get_tasks(
            status_filter=self.status_filter,
            category_filter=self.category_filter,
            search_text=self.search_text
        )

        if not tasks:
            empty_label = Label(
                text="Задач не найдено",
                color=TEXT_MUTED,
                size_hint_y=None,
                height=dp(100),
                halign="center",
                valign="middle",
                font_size=FONT_SIZE,
                bold=True
            )
            self.task_list_layout.add_widget(empty_label)
        else:
            for task in tasks:
                row = TaskRow(
                    task=task,
                    on_edit=self.edit_task,
                    on_delete=self.delete_task,
                    on_complete=self.complete_task,
                    on_select=self.toggle_select_task,
                    is_selected=(task.id in self.selected_task_ids),
                    is_archive=False
                )
                self.task_list_layout.add_widget(row)
        self._update_batch_actions_visibility()

    def add_task(self):
        form = TaskFormPopup(on_save=self._on_task_saved)
        form.open()

    def edit_task(self, task_id):
        task = self.service.get_task(task_id)
        if task:
            form = TaskFormPopup(on_save=self._on_task_saved, task=task)
            form.open()

    def _on_task_saved(self, task_data, task_id=None):
        self.service.save_task(task_data, task_id)
        self.on_tasks_changed()

    def delete_task(self, task_id):
        self.service.delete_task(task_id)
        self.selected_task_ids.discard(task_id)
        self.on_tasks_changed()

    def complete_task(self, task_id):
        self.service.mark_task_done(task_id)
        self.selected_task_ids.discard(task_id)
        self.on_tasks_changed()

    def toggle_select_task(self, task_id):
        if task_id in self.selected_task_ids:
            self.selected_task_ids.remove(task_id)
        else:
            self.selected_task_ids.add(task_id)
        self.refresh_tasks()

    def _update_batch_actions_visibility(self):
        if self.selected_task_ids:
            self.batch_actions.height = dp(64)
            self.batch_actions.opacity = 1
        else:
            self.batch_actions.height = 0
            self.batch_actions.opacity = 0

    def complete_selected(self, *args):
        for t_id in list(self.selected_task_ids):
            self.service.mark_task_done(t_id)
        self.selected_task_ids.clear()
        self.on_tasks_changed()

    def delete_selected(self, *args):
        for t_id in list(self.selected_task_ids):
            self.service.delete_task(t_id)
        self.selected_task_ids.clear()
        self.on_tasks_changed()


class ArchiveScreen(Screen):
    def __init__(self, service, on_clear_all, on_tasks_changed, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.on_clear_all = on_clear_all
        self.on_tasks_changed = on_tasks_changed
        self.selected_task_ids = set()
        self.search_text = ""

        self.root_layout = RelativeLayout()
        self.main_container = BoxLayout(orientation='vertical', padding=dp(0), spacing=dp(0))

        # --- Header ---
        header = BoxLayout(size_hint_y=None, height=dp(56), padding=(dp(16), 0, dp(16), 0), spacing=dp(8))
        header.add_widget(Label(
            text="Архив", 
            font_size=FONT_SIZE, 
            bold=True, 
            halign="left", 
            valign="middle",
            size_hint_x=None,
            width=dp(100)
        ))
        header.add_widget(Widget())

        clear_btn = MaterialButton(
            text="Очистить", 
            size_hint=(None, None), 
            width=dp(100), 
            height=dp(36),
            pos_hint={'center_y': 0.5},
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            font_size=FONT_SIZE,
            bold=True
        )
        clear_btn.bind(on_release=lambda *_: self.on_clear_all())
        header.add_widget(clear_btn)
        self.main_container.add_widget(header)

        # --- Search Bar ---
        search_bar = BoxLayout(size_hint_y=None, height=dp(48), padding=(dp(16), dp(4)), spacing=dp(8))
        self.search_input = MaterialTextInput(hint_text="Поиск в архиве...", multiline=False, height=dp(40))
        self.search_input.bind(text=self.on_search_change)
        search_bar.add_widget(self.search_input)
        self.main_container.add_widget(search_bar)

        self.scroll = ScrollView(do_scroll_x=False)
        self.archive_list_layout = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, padding=dp(10))
        self.archive_list_layout.bind(minimum_height=self.archive_list_layout.setter('height'))
        self.scroll.add_widget(self.archive_list_layout)
        self.main_container.add_widget(self.scroll)

        # --- Batch Actions ---
        self.batch_actions = MaterialCard(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            opacity=0,
            padding=(dp(16), dp(8), dp(16), dp(8)),
            spacing=dp(12),
            fill_color=POPUP_SURFACE,
            radius=0
        )
        btn_restore = FilledButton(text="Восстановить", size_hint_x=1, height=dp(40), font_size=FONT_SIZE, bold=True)
        btn_restore.bind(on_release=self.restore_selected)
        btn_delete = DangerButton(text="Удалить", size_hint_x=1, height=dp(40), font_size=FONT_SIZE, bold=True)
        btn_delete.bind(on_release=self.delete_selected)
        self.batch_actions.add_widget(btn_restore)
        self.batch_actions.add_widget(btn_delete)
        self.main_container.add_widget(self.batch_actions)

        self.root_layout.add_widget(self.main_container)
        self.add_widget(self.root_layout)
        self.refresh_archive()

    def on_search_change(self, instance, value):
        self.search_text = value
        self.refresh_archive()

    def refresh_archive(self):
        self.archive_list_layout.clear_widgets()
        tasks = self.service.get_archived_tasks(search_text=self.search_text)

        if not tasks:
            empty_label = Label(
                text="В архиве пусто",
                color=TEXT_MUTED,
                size_hint_y=None,
                height=dp(100),
                halign="center",
                valign="middle",
                font_size=FONT_SIZE,
                bold=True
            )
            self.archive_list_layout.add_widget(empty_label)
        else:
            for task in tasks:
                row = TaskRow(
                    task=task,
                    on_edit=lambda t_id: None,
                    on_delete=self.delete_archive_task,
                    on_complete=self.restore_archive_task,
                    on_select=self.toggle_select_task,
                    is_selected=(task.id in self.selected_task_ids),
                    is_archive=True
                )
                self.archive_list_layout.add_widget(row)
        self._update_batch_actions_visibility()

    def delete_archive_task(self, task_id):
        self.service.delete_task(task_id)
        self.selected_task_ids.discard(task_id)
        self.on_tasks_changed()

    def restore_archive_task(self, task_id):
        self.service.restore_task(task_id)
        self.selected_task_ids.discard(task_id)
        self.on_tasks_changed()

    def toggle_select_task(self, task_id):
        if task_id in self.selected_task_ids:
            self.selected_task_ids.remove(task_id)
        else:
            self.selected_task_ids.add(task_id)
        self.refresh_archive()

    def _update_batch_actions_visibility(self):
        if self.selected_task_ids:
            self.batch_actions.height = dp(64)
            self.batch_actions.opacity = 1
        else:
            self.batch_actions.height = 0
            self.batch_actions.opacity = 0

    def restore_selected(self, *args):
        for t_id in list(self.selected_task_ids):
            self.service.restore_task(t_id)
        self.selected_task_ids.clear()
        self.on_tasks_changed()

    def delete_selected(self, *args):
        for t_id in list(self.selected_task_ids):
            self.service.delete_task(t_id)
        self.selected_task_ids.clear()
        self.on_tasks_changed()
