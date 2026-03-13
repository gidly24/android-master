from calendar import monthrange
from datetime import date, datetime, timedelta

from models import CATEGORIES, PRIORITY_OPTIONS, RECURRENCE_OPTIONS, Task


class TaskService:
    """Business logic for task management."""

    def __init__(self, database):
        self.database = database

    def initialize_demo_data(self):
        if self.database.count_tasks() > 0:
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
                recurrence="ежемесячно",
                priority="высокий",
                status="активна",
            ),
            Task(
                id=None,
                title="Принять витамины",
                description="Утренний прием витаминов после завтрака.",
                category="лекарства",
                due_date=today.isoformat(),
                recurrence="ежедневно",
                priority="средний",
                status="активна",
            ),
            Task(
                id=None,
                title="Оплатить подписку на музыку",
                description="Проверить списание и текущий тариф.",
                category="подписки",
                due_date=(today - timedelta(days=1)).isoformat(),
                recurrence="ежемесячно",
                priority="средний",
                status="активна",
            ),
            Task(
                id=None,
                title="Полить растения",
                description="Полив комнатных растений в гостиной.",
                category="бытовые дела",
                due_date=(today + timedelta(days=3)).isoformat(),
                recurrence="еженедельно",
                priority="низкий",
                status="активна",
            ),
            Task(
                id=None,
                title="Подать заявление на пропуск",
                description="Разовая задача для университета.",
                category="другое",
                due_date=(today + timedelta(days=5)).isoformat(),
                recurrence="одноразовая",
                priority="высокий",
                status="активна",
            ),
        ]

        for task in demo_tasks:
            self.database.create_task(task)
        self.update_overdue_tasks()

    def get_tasks(self, status_filter="все", category_filter="все", search_text=""):
        self.update_overdue_tasks()
        tasks = self.database.get_all_tasks()
        result = []

        for task in tasks:
            if status_filter != "все" and task.status != status_filter:
                continue
            if category_filter != "все" and task.category != category_filter:
                continue
            if search_text and search_text.lower() not in task.title.lower():
                continue
            result.append(task)
        return result

    def get_task(self, task_id: int):
        self.update_overdue_tasks()
        return self.database.get_task(task_id)

    def save_task(self, task_data: dict, task_id=None):
        self._validate_task_data(task_data)
        status = self.calculate_status(task_data["due_date"], task_data.get("status", "активна"))
        task = Task(
            id=task_id,
            title=task_data["title"].strip(),
            description=task_data["description"].strip(),
            category=task_data["category"],
            due_date=task_data["due_date"],
            recurrence=task_data["recurrence"],
            priority=task_data["priority"],
            status=status,
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
        else:
            task.due_date = self.get_next_due_date(task.due_date, task.recurrence)
            task.status = "активна"
        self.database.update_task(task)

    def update_overdue_tasks(self):
        today = date.today()
        tasks = self.database.get_all_tasks()

        for task in tasks:
            if task.status == "выполнена":
                continue

            due_date = self.parse_date(task.due_date)
            new_status = "просрочена" if due_date < today else "активна"
            if task.status != new_status:
                task.status = new_status
                self.database.update_task(task)

    def get_statistics(self):
        self.update_overdue_tasks()
        tasks = self.database.get_all_tasks()
        return {
            "Всего задач": len(tasks),
            "Активных": len([task for task in tasks if task.status == "активна"]),
            "Выполненных": len([task for task in tasks if task.status == "выполнена"]),
            "Просроченных": len([task for task in tasks if task.status == "просрочена"]),
        }

    @staticmethod
    def calculate_status(due_date_text: str, current_status: str) -> str:
        if current_status == "выполнена":
            return "выполнена"
        due_date = TaskService.parse_date(due_date_text)
        return "просрочена" if due_date < date.today() else "активна"

    @staticmethod
    def parse_date(value: str) -> date:
        return datetime.strptime(value, "%Y-%m-%d").date()

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
    def _validate_task_data(task_data: dict):
        if not task_data["title"].strip():
            raise ValueError("Введите название задачи.")
        if task_data["category"] not in CATEGORIES:
            raise ValueError("Выберите корректную категорию.")
        if task_data["recurrence"] not in RECURRENCE_OPTIONS:
            raise ValueError("Выберите корректную периодичность.")
        if task_data["priority"] not in PRIORITY_OPTIONS:
            raise ValueError("Выберите корректный приоритет.")
        TaskService.parse_date(task_data["due_date"])
