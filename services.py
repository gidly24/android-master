from calendar import monthrange
from datetime import date, datetime, time, timedelta

from models import CATEGORIES, PRIORITY_OPTIONS, RECURRENCE_OPTIONS, Task


class TaskService:
    """Business logic for task management."""

    DEMO_DATA_STATE_KEY = "demo_data_initialized"

    def __init__(self, database):
        self.database = database

    def initialize_demo_data(self):
        if self._is_demo_data_initialized():
            self.update_overdue_tasks()
            return

        today = date.today()
        demo_tasks = [
            Task(
                id=None,
                title="Оплатить интернет",
                description="Проверить баланс и оплатить домашний интернет.",
                category="платежи",
                due_date=(today + timedelta(days=2)).isoformat(),
                due_time="18:00",
                recurrence="ежемесячно",
                priority="высокий",
                status="активна",
                is_archived=0,
            ),
            Task(
                id=None,
                title="Принять витамины",
                description="Утренний прием витаминов после завтрака.",
                category="лекарства",
                due_date=today.isoformat(),
                due_time="09:00",
                recurrence="ежедневно",
                priority="средний",
                status="активна",
                is_archived=0,
            ),
            Task(
                id=None,
                title="Оплатить подписку на музыку",
                description="Проверить списание и текущий тариф.",
                category="подписки",
                due_date=(today - timedelta(days=1)).isoformat(),
                due_time="12:00",
                recurrence="ежемесячно",
                priority="средний",
                status="активна",
                is_archived=0,
            ),
            Task(
                id=None,
                title="Полить растения",
                description="Полив комнатных растений в гостиной.",
                category="бытовые дела",
                due_date=(today + timedelta(days=3)).isoformat(),
                due_time="20:00",
                recurrence="еженедельно",
                priority="низкий",
                status="активна",
                is_archived=0,
            ),
            Task(
                id=None,
                title="Подать заявление на пропуск",
                description="Разовая задача для университета.",
                category="другое",
                due_date=(today + timedelta(days=5)).isoformat(),
                due_time="16:00",
                recurrence="одноразовая",
                priority="высокий",
                status="активна",
                is_archived=0,
            ),
        ]

        for task in demo_tasks:
            self.database.create_task(task)
        self._mark_demo_data_initialized()
        self.update_overdue_tasks()

    def _is_demo_data_initialized(self) -> bool:
        if self.database.get_app_state(self.DEMO_DATA_STATE_KEY) == "1":
            return True

        if not self.database.was_created:
            self._mark_demo_data_initialized()
            return True

        return False

    def _mark_demo_data_initialized(self):
        self.database.set_app_state(self.DEMO_DATA_STATE_KEY, "1")

    def get_tasks(self, status_filter="все", category_filter="все", search_text=""):
        self.update_overdue_tasks()
        tasks = self.database.get_all_tasks()
        result = []
        normalized_status = (status_filter or "Все").strip().lower()
        normalized_category = (category_filter or "Все").strip().lower()

        for task in tasks:
            if task.is_archived:
                continue
            if normalized_status != "все" and task.status.lower() != normalized_status:
                continue
            if normalized_category != "все" and task.category.lower() != normalized_category:
                continue
            if search_text and search_text.lower() not in task.title.lower():
                continue
            result.append(task)
        return result

    def get_task(self, task_id: int):
        self.update_overdue_tasks()
        return self.database.get_task(task_id)

    def get_archived_tasks(self, search_text=""):
        tasks = self.database.get_archived_tasks()
        if not search_text:
            return tasks
        normalized_search = search_text.lower().strip()
        return [task for task in tasks if normalized_search in task.title.lower()]

    def save_task(self, task_data: dict, task_id=None):
        self._validate_task_data(task_data)
        existing_task = self.database.get_task(task_id) if task_id else None
        status = self.calculate_status(
            task_data["due_date"],
            task_data["due_time"],
            task_data.get("status", "активна"),
        )
        task = Task(
            id=task_id,
            title=task_data["title"].strip(),
            description=task_data["description"].strip(),
            category=task_data["category"].strip().lower(),
            due_date=task_data["due_date"],
            due_time=task_data["due_time"],
            recurrence=task_data["recurrence"].strip().lower(),
            priority=task_data["priority"].strip().lower(),
            status=status,
            is_archived=existing_task.is_archived if existing_task else 0,
            archived_at=existing_task.archived_at if existing_task else None,
        )

        if task_id is None:
            return self.database.create_task(task)

        self.database.update_task(task)
        return task_id

    def delete_task(self, task_id: int):
        self.database.delete_task(task_id)

    def mark_task_done(self, task_id: int):
        task = self.database.get_task(task_id)
        if not task:
            return

        if task.recurrence == "одноразовая":
            task.status = "выполнена"
            task.is_archived = 1
            task.archived_at = datetime.now().isoformat(timespec="seconds")
        else:
            task.due_date = self.get_next_due_date(task.due_date, task.recurrence)
            task.due_time = task.due_time or "23:59"
            task.status = "активна"
            task.is_archived = 0
            task.archived_at = None
        self.database.update_task(task)

    def update_overdue_tasks(self):
        now = datetime.now()
        tasks = self.database.get_all_tasks()

        for task in tasks:
            if task.is_archived:
                continue
            if task.status == "выполнена":
                continue

            due_at = self.parse_due_datetime(task.due_date, task.due_time)
            new_status = "просрочена" if due_at < now else "активна"
            if task.status != new_status:
                task.status = new_status
                self.database.update_task(task)

    def get_statistics(self):
        self.update_overdue_tasks()
        tasks = self.database.get_all_tasks()
        return {
            "Всего задач": len([task for task in tasks if not task.is_archived]),
            "Активных": len([task for task in tasks if task.status == "активна" and not task.is_archived]),
            "Выполненных": len([task for task in tasks if task.status == "выполнена" and task.is_archived]),
            "Просроченных": len([task for task in tasks if task.status == "просрочена" and not task.is_archived]),
        }

    @staticmethod
    def calculate_status(due_date_text: str, due_time_text: str, current_status: str) -> str:
        if current_status.strip().lower() == "выполнена":
            return "выполнена"
        due_at = TaskService.parse_due_datetime(due_date_text, due_time_text)
        return "просрочена" if due_at < datetime.now() else "активна"

    @staticmethod
    def parse_date(value: str) -> date:
        return datetime.strptime(value, "%Y-%m-%d").date()

    @staticmethod
    def parse_time(value: str) -> time:
        return datetime.strptime(value, "%H:%M").time()

    @staticmethod
    def parse_due_datetime(due_date_text: str, due_time_text: str) -> datetime:
        due_date = TaskService.parse_date(due_date_text)
        due_time = TaskService.parse_time(due_time_text or "23:59")
        return datetime.combine(due_date, due_time)

    @staticmethod
    def get_next_due_date(current_due_date: str, recurrence: str) -> str:
        base_date = max(TaskService.parse_date(current_due_date), date.today())

        if recurrence == "ежедневно":
            next_date = base_date + timedelta(days=1)
        elif recurrence == "еженедельно":
            next_date = base_date + timedelta(days=7)
        elif recurrence == "ежемесячно":
            year = base_date.year
            month = base_date.month + 1
            if month > 12:
                month = 1
                year += 1
            day = min(base_date.day, monthrange(year, month)[1])
            next_date = date(year, month, day)
        else:
            next_date = base_date
        return next_date.isoformat()

    @staticmethod
    def get_countdown_text(task: Task) -> str:
        if task.status == "выполнена":
            return "Задача завершена"

        delta = TaskService.parse_due_datetime(task.due_date, task.due_time) - datetime.now()
        total_seconds = int(delta.total_seconds())
        prefix = "Осталось" if total_seconds >= 0 else "Просрочена на"
        total_seconds = abs(total_seconds)

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, _ = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days}д")
        if hours or days:
            parts.append(f"{hours}ч")
        parts.append(f"{minutes}м")
        return f"{prefix}: {' '.join(parts[:3])}"

    @staticmethod
    def _validate_task_data(task_data: dict):
        if not task_data["title"].strip():
            raise ValueError("Введите название задачи.")
        if task_data["category"].strip().lower() not in CATEGORIES:
            raise ValueError("Выберите корректную категорию.")
        if task_data["recurrence"].strip().lower() not in RECURRENCE_OPTIONS:
            raise ValueError("Выберите корректную периодичность.")
        if task_data["priority"].strip().lower() not in PRIORITY_OPTIONS:
            raise ValueError("Выберите корректный приоритет.")
        TaskService.parse_date(task_data["due_date"])
        TaskService.parse_time(task_data["due_time"])
