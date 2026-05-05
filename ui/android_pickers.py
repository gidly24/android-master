from datetime import date as date_cls

from kivy.clock import Clock
from kivy.utils import platform


def _is_android():
    return platform == "android"


def open_date_picker(initial_date: str, on_select, on_cancel=None):
    """Open native Android DatePickerDialog. Returns False if not on Android."""
    if not _is_android():
        return False

    try:
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        DatePickerDialog = autoclass("android.app.DatePickerDialog")
        Calendar = autoclass("java.util.Calendar")

        try:
            d = date_cls.fromisoformat(initial_date)
        except (ValueError, TypeError):
            d = date_cls.today()

        year, month, day = d.year, d.month - 1, d.day  # month is 0-based in Java

        @run_on_ui_thread
        def show():
            def on_set(_dialog, y, m, day_of_month):
                result = f"{y:04d}-{m + 1:02d}-{day_of_month:02d}"
                Clock.schedule_once(lambda *_: on_select(result), 0)

            def on_dismiss(_dialog):
                # called when dialog is dismissed without selection
                pass

            dialog = DatePickerDialog(
                PythonActivity.mActivity,
                on_set,
                year,
                month,
                day,
            )
            dialog.setOnCancelListener(
                lambda *_: Clock.schedule_once(lambda *__: on_cancel() if on_cancel else None, 0)
            )
            dialog.show()

        show()
        return True

    except Exception:
        return False


def open_time_picker(initial_time: str, on_select, on_cancel=None):
    """Open native Android TimePickerDialog. Returns False if not on Android."""
    if not _is_android():
        return False

    try:
        from android.runnable import run_on_ui_thread
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        TimePickerDialog = autoclass("android.app.TimePickerDialog")

        hour, minute = 23, 59
        if initial_time and ":" in initial_time:
            parts = initial_time.split(":", 1)
            if parts[0].isdigit() and parts[1].isdigit():
                hour, minute = int(parts[0]), int(parts[1])

        @run_on_ui_thread
        def show():
            def on_set(_dialog, h, m):
                result = f"{h:02d}:{m:02d}"
                Clock.schedule_once(lambda *_: on_select(result), 0)

            dialog = TimePickerDialog(
                PythonActivity.mActivity,
                on_set,
                hour,
                minute,
                True,  # is24HourView
            )
            dialog.setOnCancelListener(
                lambda *_: Clock.schedule_once(lambda *__: on_cancel() if on_cancel else None, 0)
            )
            dialog.show()

        show()
        return True

    except Exception:
        return False
