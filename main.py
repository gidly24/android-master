from pathlib import Path
import sys
import os

from kivy.config import Config


def load_env_file():
    env_path = Path(__file__).parent / "config.env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


load_env_file()

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
    def build(self):
        self.title = "Task Control"
        Window.clearcolor = APP_BACKGROUND
        Window.softinput_mode = "below_target"
        if platform not in ("android", "ios"):
            Window.size = (430, 780)

        database_path = Path(__file__).resolve().parent / "tasks.db"
        self.database = DatabaseManager(database_path)
        self.service = TaskService(self.database)
        self.service.initialize_demo_data()

        try:
            self.ai_assistant = AIAssistant(task_service=self.service)
        except ValueError as e:
            print(f"Error initializing AI Assistant: {e}") # Log the error
            self.ai_assistant = None # Ensure it's None if initialization fails
        except Exception as e:
            print(f"An unexpected error occurred during AI Assistant initialization: {e}")
            self.ai_assistant = None

        self.chat_modal = ChatModal(
            agent=self.ai_assistant,
            service=self.service,
            on_tasks_changed=self.refresh_all_screens
        )
        self.screen_manager = None

        root = MaterialRoot(orientation="vertical", spacing=dp(0), padding=dp(0))
        
        # --- Табы ---
        tabs = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(2))
        self.tasks_tab = MaterialButton(
            text="Задачи", 
            fill_color=M3_PRIMARY, 
            radius=0,
            height=dp(48)
        )
        self.archive_tab = MaterialButton(
            text="Архив", 
            fill_color=POPUP_SURFACE, 
            radius=0,
            height=dp(48)
        )
        self.tasks_tab.bind(on_release=lambda *_: self.switch_screen("tasks"))
        self.archive_tab.bind(on_release=lambda *_: self.switch_screen("archive"))
        tabs.add_widget(self.tasks_tab)
        tabs.add_widget(self.archive_tab)
        root.add_widget(tabs)

        screens = self._build_screens()
        root.add_widget(screens)
        self.root_widget = root
        return root

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
        Clock.schedule_once(self._force_layout_pass, 0)
        Window.bind(size=lambda *_: Clock.schedule_once(self._force_layout_pass, 0))

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
        # Очищаем выделение при глобальном обновлении (например, после ИИ)
        self.task_list_screen.selected_task_ids.clear()
        self.task_list_screen._update_batch_actions_visibility()
        self.archive_screen.selected_task_ids.clear()
        self.archive_screen._update_batch_actions_visibility()
        
        current = self.screen_manager.current
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

    # --- Свайпы для перехода между экранами ---
    def on_touch_down(self, touch):
        if self.screen_manager:
            # Сначала сохраняем точку старта в touch.ud (пользовательские данные касания)
            touch.ud['start_x'] = touch.x
            touch.ud['is_swiping'] = True
        return super().on_touch_down(touch)  # Передаем виджетам БЕЗ прерывания метода

    def on_touch_move(self, touch):
        if self.screen_manager and 'start_x' in touch.ud and touch.ud['is_swiping']:
            move_x = touch.x - touch.ud['start_x']
            # Если это явный горизонтальный жест (свайп длиннее 10dp и шире, чем выше)
            if abs(move_x) > dp(10) and abs(move_x) > abs(touch.dy):
                # Перехватываем управление у ScrollView, чтобы список не дергался по вертикали
                return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.screen_manager or 'start_x' not in touch.ud or not touch.ud['is_swiping']:
            return super().on_touch_up(touch)

        move_x = touch.x - touch.ud['start_x']
        swipe_threshold = dp(70)  # Увеличим порог, чтобы не было ложных срабатываний
        current_screen_name = self.screen_manager.current

        # Свайп вправо (движение пальца слева направо) -> открываем архив
        if move_x > swipe_threshold and current_screen_name == 'tasks':
            self.switch_screen("archive")
            touch.ud['is_swiping'] = False
            return True

        # Свайп влево (движение пальца справа налево) -> возвращаемся к задачам
        elif move_x < -swipe_threshold and current_screen_name == 'archive':
            self.switch_screen("tasks")
            touch.ud['is_swiping'] = False
            return True

        touch.ud['is_swiping'] = False
        return super().on_touch_up(touch)


if __name__ == "__main__":
    TaskControlApp().run()
