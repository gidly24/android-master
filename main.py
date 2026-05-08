from pathlib import Path
import sys

from kivy.config import Config

if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

Config.set("graphics", "multisamples", "8")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import NoTransition, ScreenManager
from kivy.utils import platform

from ai_agent import TaskAIAgent
from database import DatabaseManager
from services import TaskService
from ui.chat_screen import ChatModal
from ui.components import APP_BACKGROUND, INPUT_FILL, M3_PRIMARY, TEXT_PRIMARY, MaterialButton, MaterialCard, MaterialRoot
from ui.screens import ArchiveScreen, TaskListScreen


class TaskControlApp(App):
    def build(self):
        self.title = "Task Control"
        Window.clearcolor = APP_BACKGROUND
        if platform not in ("android", "ios"):
            Window.size = (430, 780)

        database_path = Path(__file__).resolve().parent / "tasks.db"
        self.database = DatabaseManager(database_path)
        self.service = TaskService(self.database)
        self.ai_agent = TaskAIAgent(self.service)
        self.service.initialize_demo_data()
        self.chat_modal = ChatModal(agent=self.ai_agent, on_tasks_changed=self.refresh_all_screens)

        root = MaterialRoot(orientation="vertical", spacing=dp(0), padding=dp(0))
        navigation = self._build_navigation()
        screens = self._build_screens()
        root.add_widget(navigation)
        root.add_widget(screens)
        self._update_navigation("tasks")
        self.root_widget = root
        return root

    def on_start(self):
        Clock.schedule_once(self._force_layout_pass, 0)
        Window.bind(size=lambda *_: Clock.schedule_once(self._force_layout_pass, 0))

    def _build_navigation(self):
        navigation = MaterialCard(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(52),
            spacing=dp(0),
            padding=dp(0),
            fill_color=APP_BACKGROUND,
            radius=0,
        )
        tasks_button = MaterialButton(text="Задачи", radius=0, size_hint_y=1)
        tasks_button.bind(on_release=lambda *_: self.switch_screen("tasks"))
        archive_button = MaterialButton(text="Архив", radius=0, size_hint_y=1)
        archive_button.bind(on_release=lambda *_: self.switch_screen("archive"))
        self.nav_buttons = {"tasks": tasks_button, "archive": archive_button}
        navigation.add_widget(tasks_button)
        navigation.add_widget(archive_button)
        return navigation

    def _build_screens(self):
        self.screen_manager = ScreenManager(transition=NoTransition())
        self.task_list_screen = TaskListScreen(
            name="tasks",
            service=self.service,
            on_tasks_changed=self.refresh_all_screens,
            on_open_chat=self.open_chat_modal,
        )
        self.archive_screen = ArchiveScreen(name="archive", service=self.service, on_clear_all=self.clear_archive)
        self.screen_manager.add_widget(self.task_list_screen)
        self.screen_manager.add_widget(self.archive_screen)
        return self.screen_manager

    def refresh_all_screens(self):
        current = self.screen_manager.current
        self.task_list_screen.refresh_tasks()
        if current == "archive":
            self.archive_screen.refresh_archive()

    def clear_archive(self):
        self.service.clear_archived_tasks()
        self.refresh_all_screens()

    def switch_screen(self, screen_name):
        self.screen_manager.current = screen_name
        self._update_navigation(screen_name)
        if screen_name == "archive":
            self.archive_screen.refresh_archive()

    def open_chat_modal(self):
        if not self.chat_modal._window:
            self.chat_modal.open()

    def _update_navigation(self, active_name):
        for name, button in self.nav_buttons.items():
            if name == active_name:
                button.set_palette(fill_color=M3_PRIMARY, border_color=M3_PRIMARY, text_color=TEXT_PRIMARY)
            else:
                button.set_palette(
                    fill_color=INPUT_FILL,
                    border_color=INPUT_FILL,
                    text_color=TEXT_PRIMARY,
                )

    def _force_layout_pass(self, *_):
        if hasattr(self.root_widget, "do_layout"):
            self.root_widget.do_layout()


if __name__ == "__main__":
    TaskControlApp().run()
