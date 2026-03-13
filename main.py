from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import NoTransition, ScreenManager

from database import DatabaseManager
from services import TaskService
from ui.components import GlassButton, GlassPane, GlassRoot, PrimaryGlassButton
from ui.screens import StatsScreen, TaskListScreen


class TaskControlApp(App):
    """Main application class."""

    def build(self):
        self.title = "Контроль сроков задач"
        Window.clearcolor = (0.04, 0.06, 0.1, 1)
        Window.size = (430, 780)

        database_path = Path(__file__).resolve().parent / "tasks.db"
        self.database = DatabaseManager(database_path)
        self.service = TaskService(self.database)
        self.service.initialize_demo_data()

        root = GlassRoot(orientation="vertical", spacing=dp(10), padding=dp(12))
        root.add_widget(self._build_navigation())
        root.add_widget(self._build_screens())
        self.root_widget = root
        return root

    def on_start(self):
        for delay in (0, 0.1, 0.25, 0.5, 1.0):
            Clock.schedule_once(self._force_layout_pass, delay)
        Window.bind(size=lambda *_: Clock.schedule_once(self._force_layout_pass, 0))

    def _build_navigation(self):
        navigation = GlassPane(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(64),
            spacing=dp(10),
            padding=dp(10),
        )

        tasks_button = PrimaryGlassButton(text="Задачи")
        tasks_button.bind(on_release=lambda *_: self.switch_screen("tasks"))

        stats_button = GlassButton(text="Статистика")
        stats_button.bind(on_release=lambda *_: self.switch_screen("stats"))

        self.nav_buttons = {"tasks": tasks_button, "stats": stats_button}
        navigation.add_widget(tasks_button)
        navigation.add_widget(stats_button)
        return navigation

    def _build_screens(self):
        self.screen_manager = ScreenManager(transition=NoTransition())
        self.task_list_screen = TaskListScreen(name="tasks", service=self.service)
        self.stats_screen = StatsScreen(name="stats", service=self.service)
        self.screen_manager.add_widget(self.task_list_screen)
        self.screen_manager.add_widget(self.stats_screen)
        return self.screen_manager

    def switch_screen(self, screen_name):
        self.screen_manager.current = screen_name
        self._update_navigation(screen_name)

        if screen_name == "tasks":
            self.task_list_screen.refresh_tasks()
        if screen_name == "stats":
            self.stats_screen.refresh_stats()

        Clock.schedule_once(self._force_layout_pass, 0)

    def _update_navigation(self, active_name):
        for name, button in self.nav_buttons.items():
            if name == active_name:
                button.set_palette(
                    fill_color=(0.2, 0.47, 0.96, 1),
                    border_color=(0.48, 0.67, 1, 0.9),
                    text_color=(1, 1, 1, 1),
                )
            else:
                button.set_palette(
                    fill_color=(0.1, 0.14, 0.22, 0.98),
                    border_color=(0.27, 0.35, 0.52, 0.9),
                    text_color=(0.95, 0.97, 1, 1),
                )

    def _force_layout_pass(self, *_):
        self._layout_recursive(self.root_widget)

    def _layout_recursive(self, widget):
        if hasattr(widget, "do_layout"):
            widget.do_layout()
        for child in widget.children:
            self._layout_recursive(child)


if __name__ == "__main__":
    TaskControlApp().run()
