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
        self.service = TaskService(self.database, self._schedule_task_reminder)
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

        root = MaterialRoot(orientation="vertical", spacing=dp(16), padding=dp(16))
        
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
        self._setup_notification_channel()
        self.check_intent_for_task()

        # Перехват кликов, если приложение уже висит в фоне
        if platform == "android":
            from android.activity import bind as android_bind
            android_bind(on_new_intent=lambda intent: Clock.schedule_once(self.check_intent_for_task, 0.5))

        # Планируем уведомления для существующих задач
        if platform == "android":
            self._schedule_all_reminders()

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

    def _schedule_all_reminders(self):
        """Планирует уведомления для всех активных задач"""
        tasks = self.service.database.get_all_tasks()
        for task in tasks:
            if not task.is_archived and task.due_date:
                self._schedule_reminder(task.id, task.title, task.due_date, task.due_time, "start")
                self._schedule_reminder(task.id, task.title, task.due_date, task.due_time, "before")

    def _schedule_task_reminder(self, task_id: int, title: str, due_date: str, due_time: str, action="schedule"):
        """Схема для планирования уведомлений при создании/изменении задачи"""
        if action == "cancel":
            self._cancel_reminders(task_id)
        else:
            self._schedule_reminder(task_id, title, due_date, due_time, "start")
            self._schedule_reminder(task_id, title, due_date, due_time, "before")

    def _cancel_reminders(self, task_id: int):
        """Отменяет запланированные уведомления для задачи"""
        if platform != "android":
            return

        from jnius import autoclass, cast
        PendingIntent = autoclass("android.app.PendingIntent")
        AlarmManager = autoclass("android.app.AlarmManager")
        Context = autoclass("android.content.Context")
        Intent = autoclass("android.content.Intent")

        python_activity = autoclass("org.kivy.android.PythonActivity")
        context = cast("android.content.Context", python_activity.mActivity)

        # Отменяем оба уведомления: "вовремя" и "за час"
        for reminder_type in ["start", "before"]:
            req_code = task_id * (1 if reminder_type == "start" else 2)
            
            intent = Intent()
            intent.setClassName(context.getPackageName(), "org.kivy.android.PythonBroadcastReceiver")
            intent.setAction("com.taskcontrol.reminder")
            intent.putExtra("task_id", task_id)
            intent.putExtra("type", reminder_type)

            flags = PendingIntent.FLAG_UPDATE_CURRENT
            if hasattr(PendingIntent, "FLAG_IMMUTABLE"):
                flags |= PendingIntent.FLAG_IMMUTABLE

            pending_intent = PendingIntent.getBroadcast(context, req_code, intent, flags)
            
            alarm_manager = context.getSystemService(Context.ALARM_SERVICE)
            alarm_manager.cancel(pending_intent)

    def _setup_notification_channel(self):
        """Создает канал уведомлений для Android 8+"""
        if platform != "android":
            return

        from jnius import autoclass, cast
        from android import api_version

        if api_version < 26:
            return

        NotificationManager = autoclass("android.app.NotificationManager")
        NotificationChannel = autoclass("android.app.NotificationChannel")
        Context = autoclass("android.content.Context")

        context = cast("android.content.Context", autoclass("org.kivy.android.PythonActivity").mActivity)
        channel_id = "task_reminder_channel"
        channel_name = "Напоминания о задачах"
        channel_description = "Уведомления о предстоящих задачах"
        importance = NotificationManager.IMPORTANCE_DEFAULT

        notification_channel = NotificationChannel(channel_id, channel_name, importance)
        notification_channel.setDescription(channel_description)

        notification_service = context.getSystemService(Context.NOTIFICATION_SERVICE)
        notification_service.createNotificationChannel(notification_channel)

    def _show_notification(self, title, message, task_id=None):
        """Отображает нативное уведомление с действием открытия приложения"""
        if platform != "android":
            return

        from jnius import autoclass, cast
        from android import api_version

        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        context = cast("android.content.Context", PythonActivity.mActivity)

        NotificationCompat = autoclass("androidx.core.app.NotificationCompat")
        NotificationManager = autoclass("android.app.NotificationManager")
        Intent = autoclass("android.content.Intent")
        PendingIntent = autoclass("android.app.PendingIntent")

        # Интент для открытия приложения при клике
        notification_intent = Intent(context, PythonActivity)
        notification_intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP)

        if task_id:
            notification_intent.putExtra("open_task_id", task_id)

        # Настройка флагов для Android 12+
        pending_flags = PendingIntent.FLAG_UPDATE_CURRENT
        if hasattr(PendingIntent, "FLAG_IMMUTABLE"):
            pending_flags |= PendingIntent.FLAG_IMMUTABLE

        req_code = task_id or 0
        content_intent = PendingIntent.getActivity(
            context, req_code, notification_intent, pending_flags
        )

        builder = NotificationCompat.Builder(context, "task_reminder_channel")
        builder.setContentTitle(title)
        builder.setContentText(message)
        builder.setSmallIcon(context.getApplicationInfo().icon)
        builder.setAutoCancel(True)
        builder.setContentIntent(content_intent)

        if api_version >= 26:
            builder.setChannelId("task_reminder_channel")

        notification = builder.build()
        notification_service = context.getSystemService(Context.NOTIFICATION_SERVICE)
        notification_service.notify(req_code, notification)

    def _schedule_reminder(self, task_id: int, title: str, due_date: str, due_time: str,
                           reminder_type: str = "start"):
        """Планирует срабатывание AlarmManager на определенное время"""
        if platform != "android":
            return

        from jnius import autoclass, cast
        from datetime import datetime, timedelta

        if not due_date:
            return

        # Парсим дату и время задачи
        try:
            time_str = due_time if due_time else "00:00"
            dt = datetime.fromisoformat(f"{due_date}T{time_str}")
        except (ValueError, TypeError):
            return

        if reminder_type == "before":
            trigger_time = dt - timedelta(hours=1)
        else:
            trigger_time = dt

        # Если время уже прошло, не планируем
        if trigger_time < datetime.now():
            return

        trigger_millis = int(trigger_time.timestamp() * 1000)

        Context = autoclass("android.content.Context")
        Intent = autoclass("android.content.Intent")
        PendingIntent = autoclass("android.app.PendingIntent")
        AlarmManager = autoclass("android.app.AlarmManager")

        python_activity = autoclass("org.kivy.android.PythonActivity")
        context = cast("android.content.Context", python_activity.mActivity)

        # ВАЖНО: Используем интент, направленный на наш будущий BroadcastReceiver
        intent = Intent()
        intent.setClassName(context.getPackageName(), "org.kivy.android.PythonBroadcastReceiver")
        intent.setAction("com.taskcontrol.reminder")
        intent.putExtra("task_id", task_id)
        intent.putExtra("title", title)
        intent.putExtra("type", reminder_type)

        flags = PendingIntent.FLAG_UPDATE_CURRENT
        if hasattr(PendingIntent, "FLAG_IMMUTABLE"):
            flags |= PendingIntent.FLAG_IMMUTABLE

        # Уникальный requestCode для разделения "вовремя" и "за час"
        req_code = task_id * (1 if reminder_type == "start" else 2)
        pending_intent = PendingIntent.getBroadcast(context, req_code, intent, flags)

        alarm_manager = context.getSystemService(Context.ALARM_SERVICE)
        alarm_manager.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            trigger_millis,
            pending_intent
        )

    def check_intent_for_task(self, *args):
        """Проверяет, было ли приложение открыто из уведомления"""
        if platform != "android":
            return

        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        intent = activity.getIntent()

        if intent and intent.hasExtra("open_task_id"):
            task_id = intent.getIntExtra("open_task_id", 0)
            print(f"[Уведомления] Кликнули по задаче с ID: {task_id}")

            # TODO: Здесь можно добавить переключение экрана или фокус на задачу
            # Например: self.switch_screen("tasks")

            intent.removeExtra("open_task_id")


if __name__ == "__main__":
    TaskControlApp().run()
