from pathlib import Path
import sys
import os
from datetime import datetime

def global_exception_handler(exctype, value, tb):
    pass

sys.excepthook = global_exception_handler
from kivy.config import Config

Config.set("graphics", "multisamples", "8")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition, ScreenManager
from kivy.utils import platform

from ai_assistant import AIAssistant
from database import DatabaseManager
from services import TaskService
from ui.chat_screen import ChatModal
from ui.components import (
    APP_BACKGROUND,
    M3_PRIMARY,
    POPUP_SURFACE,
    MaterialButton,
    MaterialRoot,
)
from ui.screens import ArchiveScreen, TaskListScreen


class TaskControlApp(App):
    def _load_config(self):
        config_path = Path(__file__).resolve().parent / "config.env"
        if config_path.exists():
            with open(config_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()

    def build(self):
        self._load_config()
        self.title = "Task Control"
        Window.clearcolor = APP_BACKGROUND
        Window.softinput_mode = "below_target"

        database_path = Path(__file__).resolve().parent / "tasks.db"
        self.database = DatabaseManager(database_path)
        self.service = TaskService(self.database, self._show_notification)
        self.service.initialize_demo_data()

        try:
            self.ai_assistant = AIAssistant(task_service=self.service)
        except ValueError:
            self.ai_assistant = None
        except Exception:
            self.ai_assistant = None

        self.chat_modal = ChatModal(
            agent=self.ai_assistant,
            service=self.service,
            on_tasks_changed=self.refresh_all_screens
        )
        self.screen_manager = None

        root = MaterialRoot(orientation="vertical", spacing=dp(16), padding=dp(16))

        tabs = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(2))
        self.tasks_tab = MaterialButton(text="Задачи", fill_color=M3_PRIMARY, radius=0, height=dp(48))
        self.archive_tab = MaterialButton(text="Архив", fill_color=POPUP_SURFACE, radius=0, height=dp(48))
        self.tasks_tab.bind(on_release=lambda *_: self.switch_screen("tasks"))
        self.archive_tab.bind(on_release=lambda *_: self.switch_screen("archive"))
        tabs.add_widget(self.tasks_tab)
        tabs.add_widget(self.archive_tab)
        root.add_widget(tabs)

        screens = self._build_screens()
        root.add_widget(screens)
        self.root_widget = root
        return root

    def _show_notification(self, task_id, title, due_date, due_time, action="notify"):
        # This is a placeholder that might need to be implemented for Android specifically,
        # but the user requested this mechanism.
        try:
            from android_notify import Notification
            if action == "cancel":
                pass # Handle cancellation if needed
            else:
                Notification(
                    title=f"Пора приступать: {title}",
                    message=f"Задача '{title}' должна быть выполнена сейчас ({due_date} {due_time})."
                ).send()
        except Exception as e:
            print(f"Ошибка уведомления: {e}")

    def _check_deadlines(self, dt):
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        tasks = self.database.get_tasks_due_at(date_str, time_str)
        for task in tasks:
            self._show_notification(task.id, task.title, task.due_date, task.due_time)

    def _request_android_notification_permission(self):
        if platform != "android":
            return

        try:
            from android import api_version
            if api_version < 33:
                return

            from android.permissions import Permission, check_permission, request_permissions
            if not check_permission(Permission.POST_NOTIFICATIONS):
                request_permissions([Permission.POST_NOTIFICATIONS])
        except Exception as e:
            print(f"Failed to request notification permission: {e}")

    def switch_screen(self, name):
        if self.screen_manager.current == name:
            return
        direction = "left" if name == "archive" else "right"
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = name
        self._update_tab_colors(name)

    def _update_tab_colors(self, current_name):
        if current_name == "tasks":
            self.tasks_tab.set_palette(fill_color=M3_PRIMARY)
            self.archive_tab.set_palette(fill_color=POPUP_SURFACE)
        else:
            self.tasks_tab.set_palette(fill_color=POPUP_SURFACE)
            self.archive_tab.set_palette(fill_color=M3_PRIMARY)

    def on_start(self):
        self._request_android_notification_permission()
        self.service.reschedule_android_alarms()

        Clock.schedule_once(self._force_layout_pass, 0)
        Window.bind(size=lambda *_: Clock.schedule_once(self._force_layout_pass, 0))

        if platform != "android":
            Clock.schedule_interval(self._check_deadlines, 60)

    def _build_screens(self):
        self.screen_manager = ScreenManager(transition=SlideTransition(direction='left'))
        self.task_list_screen = TaskListScreen(
            name="tasks",
            service=self.service,
            on_tasks_changed=self.refresh_all_screens,
            on_open_chat=self.open_chat_modal,
        )
        self.archive_screen = ArchiveScreen(
            name="archive",
            service=self.service,
            on_clear_all=self.clear_archive,
            on_tasks_changed=self.refresh_all_screens
        )
        self.screen_manager.add_widget(self.task_list_screen)
        self.screen_manager.add_widget(self.archive_screen)
        return self.screen_manager

    def refresh_all_screens(self):
        self.task_list_screen.selected_task_ids.clear()
        self.task_list_screen._update_batch_actions_visibility()
        self.archive_screen.selected_task_ids.clear()
        self.archive_screen._update_batch_actions_visibility()
        self.task_list_screen.refresh_tasks()
        self.archive_screen.refresh_archive()

    def clear_archive(self):
        self.service.clear_archived_tasks()
        self.refresh_all_screens()

    def open_chat_modal(self):
        if not self.chat_modal._window:
            self.chat_modal.open()

    def _force_layout_pass(self, *_):
        if hasattr(self.root_widget, "do_layout"):
            self.root_widget.do_layout()


if __name__ == "__main__":
    TaskControlApp().run()
