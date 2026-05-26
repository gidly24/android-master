from kivy.graphics import Color, Ellipse, RoundedRectangle
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


class FilterModal(ModalView):
    def __init__(self, on_apply_filters, current_status_filter, current_category_filter, **kwargs):
        super().__init__(**kwargs)
        self.on_apply_filters = on_apply_filters
        self.current_status_filter = current_status_filter
        self.current_category_filter = current_category_filter

        self.size_hint = (0.85, None)
        self.height = dp(220)
        self.background_color = TRANSPARENT_APP
        self.separator_height = 0
        self.auto_dismiss = True

        main_layout = BoxLayout(orientation='vertical', spacing=dp(0), padding=dp(16), size_hint=(1, 1))
        
        with main_layout.canvas.before:
            Color(*POPUP_SURFACE)
            self.rect = RoundedRectangle(size=main_layout.size, pos=main_layout.pos, radius=[dp(20)])
        main_layout.bind(pos=self._update_rect, size=self._update_rect)

        header = BoxLayout(size_hint_y=None, height=dp(48), padding=dp(0), spacing=dp(16))
        title_label = Label(text="Фильтры", font_size="18sp", bold=True, halign="left", valign="middle", size_hint_x=None)
        bind_text_size(title_label)
        header.add_widget(title_label)
        header.add_widget(Widget())
        close_btn = MaterialButton(text="X", size_hint=(None, None), width=dp(40), height=dp(40))
        close_btn.bind(on_release=self.dismiss)
        header.add_widget(close_btn)
        main_layout.add_widget(header)

        content = BoxLayout(orientation='vertical', spacing=dp(16), padding=dp(0), size_hint_y=None)
        
        status_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        status_row.add_widget(Label(text="Статус:", font_size=FONT_SIZE, bold=True, size_hint_x=None, width=dp(80), halign="left"))
        self.status_spinner = MaterialSpinner(
            text=self.current_status_filter.capitalize(),
            values=("Все", "Активные", "Выполненные", "Просроченные"),
            height=dp(36),
            radius=dp(18),
            size_hint_x=1
        )
        status_row.add_widget(self.status_spinner)
        content.add_widget(status_row)

        cat_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(8))
        cat_row.add_widget(Label(text="Категория:", font_size=FONT_SIZE, bold=True, size_hint_x=None, width=dp(80), halign="left"))
        cat_values = ["Все"] + [c.capitalize() for c in CATEGORIES]
        self.category_spinner = MaterialSpinner(
            text=self.current_category_filter.capitalize(),
            values=tuple(cat_values),
            height=dp(36),
            radius=dp(18),
            size_hint_x=1
        )
        cat_row.add_widget(self.category_spinner)
        content.add_widget(cat_row)
        
        main_layout.add_widget(content)

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(16), padding=dp(0))
        reset_btn = MaterialButton(text="Сбросить", size_hint_x=1, height=dp(40))
        reset_btn.bind(on_release=self._reset_filters)
        button_row.add_widget(reset_btn)
        apply_btn = FilledButton(text="Применить", size_hint_x=1, height=dp(40))
        apply_btn.bind(on_release=self._apply_filters_and_dismiss)
        button_row.add_widget(apply_btn)
        main_layout.add_widget(button_row)

        self.add_widget(main_layout)

    def _apply_filters_and_dismiss(self, *args):
        status = self.status_spinner.text.lower()
        category = self.category_spinner.text.lower()
        self.on_apply_filters(status, category)
        self.dismiss()

    def _reset_filters(self, *args):
        self.status_spinner.text = "Все"
        self.category_spinner.text = "Все"
        self.on_apply_filters("все", "все")
        self.dismiss()

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

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
        
        actions.add_widget(Widget())
        
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
        actions.add_widget(c)
        
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
        self.status_filter = "все"  # Initial filter value
        self.category_filter = "все"  # Initial filter value
        self.search_text = ""

        self.root_layout = RelativeLayout()
        self.main_container = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(16))

        # --- Header ---
        header = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(16), spacing=dp(16))
        title_label = Label(
            text="Мои задачи", 
            font_size=FONT_SIZE, 
            bold=True, 
            halign="left", 
            valign="middle",
            size_hint_x=None
        )
        bind_text_size(title_label)
        header.add_widget(title_label)
        header.add_widget(Widget())
        self.main_container.add_widget(header)
        
        # Add More button to RelativeLayout
        # More button (was self.more_button)
        self.more_button = IconCircleButton(
            icon_source=MORE_ICON,
            fallback_text="...",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            font_size="20sp",
            pos_hint={'right': 0.98, 'top': 0.98}
        )
        self.more_button.bind(on_release=self.open_filter_modal)
        self.root_layout.add_widget(self.more_button)
        
        # Create a layout for the action buttons that appear near the more button
        self.action_buttons_layout = BoxLayout(
            orientation='horizontal', 
            size_hint=(None, None), 
            size=(dp(124), dp(56)), 
            spacing=dp(12), 
            pos_hint={'right': 0.95, 'top': 0.12}
        )
        
        # Complete selected tasks button
        self.complete_selected_btn = CircleButton(
            text="Г",
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            font_size="32sp"
        )
        self.complete_selected_btn.bind(on_release=self.complete_selected)
        self.complete_selected_btn.opacity = 0
        self.complete_selected_btn.height = 0
        
        # Delete selected tasks button
        self.delete_selected_btn = CircleButton(
            text="У",
            size_hint=(None, None),
            size=(dp(56), dp(56)),
            fill_color=M3_PRIMARY,
            text_color=TEXT_PRIMARY,
            font_size="32sp"
        )
        self.delete_selected_btn.bind(on_release=self.delete_selected)
        self.delete_selected_btn.opacity = 0
        self.delete_selected_btn.height = 0
        
        # Add the action buttons to their layout
        self.action_buttons_layout.add_widget(self.complete_selected_btn)
        self.action_buttons_layout.add_widget(self.delete_selected_btn)
        
        # Add the action buttons layout to the root
        self.root_layout.add_widget(self.action_buttons_layout)

        # --- Search Bar ---
        search_bar = BoxLayout(size_hint_y=None, height=dp(48), padding=(dp(16), dp(4)), spacing=dp(8))
        self.search_input = MaterialTextInput(hint_text="Поиск задач...", multiline=False, height=dp(40))
        self.search_input.bind(text=self.on_search_change)
        search_bar.add_widget(self.search_input)
        self.main_container.add_widget(search_bar)

        # --- Removed Embedded Filters ---

        self.scroll = ScrollView(do_scroll_x=False)
        self.task_list_layout = BoxLayout(orientation='vertical', spacing=dp(16), size_hint_y=None, padding=dp(16))
        self.task_list_layout.bind(minimum_height=self.task_list_layout.setter('height'))
        self.scroll.add_widget(self.task_list_layout)
        self.main_container.add_widget(self.scroll)

        # --- Batch Actions ---
        # self.batch_actions = MaterialCard(
        #     orientation="horizontal",
        #     size_hint_y=None,
        #     height=0,
        #     opacity=0,
        #     padding=dp(16),
        #     spacing=dp(16),
        #     fill_color=POPUP_SURFACE,
        #     radius=0
        # )
        # btn_complete = FilledButton(text="Выполнить", size_hint_x=1, height=dp(40), font_size=FONT_SIZE, bold=True)
        # btn_complete.bind(on_release=self.complete_selected)
        # btn_delete = DangerButton(text="Удалить", size_hint_x=1, height=dp(40), font_size=FONT_SIZE, bold=True)
        # btn_delete.bind(on_release=self.delete_selected)
        # self.batch_actions.add_widget(btn_complete)
        # self.batch_actions.add_widget(btn_delete)
        # self.main_container.add_widget(self.batch_actions)

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

        self._update_batch_actions_visibility() # Ensure correct initial state
        self.add_widget(self.root_layout)
        self.refresh_tasks() # Call without filters initially

        # Initialize FilterModal
        self.filter_modal = FilterModal(
            on_apply_filters=self._apply_filters_from_modal,
            current_status_filter=self.status_filter,
            current_category_filter=self.category_filter
        )

    def open_filter_modal(self, *args):
        # Update modal with current filters before opening
        self.filter_modal.current_status_filter = self.status_filter
        self.filter_modal.current_category_filter = self.category_filter
        self.filter_modal.status_spinner.text = self.status_filter.capitalize()
        self.filter_modal.category_spinner.text = self.category_filter.capitalize()
        self.filter_modal.open()

    def _apply_filters_from_modal(self, status, category):
        self.status_filter = status
        self.category_filter = category
        self.refresh_tasks()

    def on_search_change(self, instance, value):
        self.search_text = value
        self.refresh_tasks()

    # Remove on_filter_change as it's now handled by the modal
    # def on_filter_change(self, instance, value):
    #     self.status_filter = self.status_spinner.text.lower()
    #     self.category_filter = self.category_spinner.text.lower()
    #     self.refresh_tasks()

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
        if hasattr(self, 'complete_selected_btn') and hasattr(self, 'delete_selected_btn'):
            if self.selected_task_ids:
                # Show the action buttons
                self.complete_selected_btn.opacity = 1
                self.complete_selected_btn.height = dp(56)
                self.delete_selected_btn.opacity = 1
                self.delete_selected_btn.height = dp(56)
                # Keep the more button visible
                self.more_button.opacity = 1
                self.more_button.height = dp(40)
            else:
                # Hide the action buttons
                self.complete_selected_btn.opacity = 0
                self.complete_selected_btn.height = 0
                self.delete_selected_btn.opacity = 0
                self.delete_selected_btn.height = 0
                # Keep the more button visible
                self.more_button.opacity = 1
                self.more_button.height = dp(40)

    def complete_selected(self, *args):
        for t_id in list(self.selected_task_ids):
            self.service.mark_task_done(t_id)
        self.selected_task_ids.clear()
        self.on_tasks_changed()
        # Ensure the buttons are hidden after completion
        self._update_batch_actions_visibility()

    def delete_selected(self, *args):
        for t_id in list(self.selected_task_ids):
            self.service.delete_task(t_id)
        self.selected_task_ids.clear()
        self.on_tasks_changed()
        # Ensure the buttons are hidden after deletion
        self._update_batch_actions_visibility()


class ArchiveScreen(Screen):
    def __init__(self, service, on_clear_all, on_tasks_changed, **kwargs):
        super().__init__(**kwargs)
        self.service = service
        self.on_clear_all = on_clear_all
        self.on_tasks_changed = on_tasks_changed
        self.selected_task_ids = set()
        self.search_text = ""

        self.root_layout = RelativeLayout()
        self.main_container = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(16))

        # --- Header ---
        header = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(16), spacing=dp(16))
        title_label = Label(
            text="Архив", 
            font_size=FONT_SIZE, 
            bold=True, 
            halign="left", 
            valign="middle",
            size_hint_x=None
        )
        bind_text_size(title_label)
        header.add_widget(title_label)
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
        self.archive_list_layout = BoxLayout(orientation='vertical', spacing=dp(16), size_hint_y=None, padding=dp(16))
        self.archive_list_layout.bind(minimum_height=self.archive_list_layout.setter('height'))
        self.scroll.add_widget(self.archive_list_layout)
        self.main_container.add_widget(self.scroll)

        # --- Batch Actions ---
        self.batch_actions = MaterialCard(
            orientation="horizontal",
            size_hint_y=None,
            height=0,
            opacity=0,
            padding=dp(16),
            spacing=dp(16),
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
        if hasattr(self, 'complete_selected_btn') and hasattr(self, 'delete_selected_btn'):
            if self.selected_task_ids:
                # Show the action buttons
                self.complete_selected_btn.opacity = 1
                self.complete_selected_btn.height = dp(56)
                self.delete_selected_btn.opacity = 1
                self.delete_selected_btn.height = dp(56)
                # Keep the more button visible
                self.more_button.opacity = 1
                self.more_button.height = dp(40)
            else:
                # Hide the action buttons
                self.complete_selected_btn.opacity = 0
                self.complete_selected_btn.height = 0
                self.delete_selected_btn.opacity = 0
                self.delete_selected_btn.height = 0
                # Keep the more button visible
                self.more_button.opacity = 1
                self.more_button.height = dp(40)

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
        # Ensure the buttons are hidden after deletion
        self._update_batch_actions_visibility()
