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
        return self.database.get_tasks_filtered(
            status_filter=(status_filter or "все").strip().lower(),
            category_filter=(category_filter or "все").strip().lower(),
            search_text=(search_text or "").strip(),
        )

    def get_task(self, task_id: int):
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

    def clear_archived_tasks(self):
        self.database.clear_archived_tasks()

    def find_tasks_by_title(self, title_query: str, include_archived: bool = False):
        normalized_query = (title_query or "").strip().lower()
        if not normalized_query:
            return []

        source_tasks = self.database.get_all_tasks() if include_archived else self.get_tasks()
        exact_matches = [task for task in source_tasks if task.title.strip().lower() == normalized_query]
        if exact_matches:
            return exact_matches

        substring_matches = [task for task in source_tasks if normalized_query in task.title.strip().lower()]
        if substring_matches:
            return substring_matches

        normalized_query_tokens = self._normalize_search_tokens(normalized_query)
        fuzzy_matches = []
        for task in source_tasks:
            title_tokens = self._normalize_search_tokens(task.title)
            if normalized_query_tokens and normalized_query_tokens.issubset(title_tokens):
                fuzzy_matches.append(task)
        return fuzzy_matches

    def mark_task_done(self, task_id: int):
        task = self.database.get_task(task_id)
        if not task:
            return

        if task.recurrence == "одноразовая" or not task.due_date:
            task.status = "выполнена"
            task.is_archived = 1
            task.archived_at = datetime.now().isoformat(timespec="seconds")
        else:
            task.due_date = self.get_next_due_date(task.due_date, task.recurrence)
            task.due_time = task.due_time or ""
            task.status = "активна"
            task.is_archived = 0
            task.archived_at = None
        self.database.update_task(task)

    def update_overdue_tasks(self):
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.database.update_overdue_statuses(now_iso)

    def get_statistics(self):
        self.update_overdue_tasks()
        s = self.database.get_stats()
        return {
            "Всего задач": s["total"],
            "Активных": s["active"],
            "Выполненных": s["completed"],
            "Просроченных": s["overdue"],
        }

    def create_task_from_ai(self, payload: dict):
        due_date_value = (payload.get("due_date") or "").strip()
        due_date_part = ""
        due_time_part = ""
        if due_date_value:
            normalized_due = due_date_value.replace("T", " ")
            if " " in normalized_due:
                due_date_part, due_time_part = normalized_due.split(" ", 1)
                due_time_part = due_time_part[:5]
            else:
                due_date_part = normalized_due
                due_time_part = ""

        recurrence_key = (payload.get("recurrence") or "").strip().lower()
        recurrence_map = {
            "": "одноразовая",
            "ежедневно": "ежедневно",
            "еженедельно": "еженедельно",
            "ежемесячно": "ежемесячно",
        }

        try:
            priority_value = int(payload.get("priority", 2))
        except (TypeError, ValueError):
            priority_value = 2

        priority_map = {1: "низкий", 2: "средний", 3: "высокий"}
        task_data = {
            "title": (payload.get("title") or "").strip(),
            "description": (payload.get("description") or "Создано через ИИ-чат").strip(),
            "category": (payload.get("category") or "другое").strip().lower(),
            "due_date": due_date_part,
            "due_time": due_time_part,
            "recurrence": recurrence_map.get(recurrence_key, "одноразовая"),
            "priority": priority_map.get(priority_value, "средний"),
            "status": "активна",
        }

        task_id = self.save_task(task_data)
        task = self.get_task(task_id)
        due_at_label = f"{task.due_date} {task.due_time}".strip()
        return {
            "task_id": task_id,
            "title": task.title,
            "answer": f"Готово, добавил задачу{' на ' + due_at_label if due_at_label else ''}.",
        }

    def delete_task_from_ai(self, payload: dict):
        task_id = payload.get("task_id")
        if task_id:
            task = self.get_task(int(task_id))
            if not task:
                return {"action": "clarify", "answer": "Не нашел такую задачу."}
            self.delete_task(task.id)
            return {"deleted": True, "task_id": task.id, "answer": f"Готово, удалил задачу «{task.title}»."}

        title_query = payload.get("title_query", "")
        active_tasks = self.get_tasks()
        if not active_tasks:
            return {"action": "clarify", "answer": "Активных задач сейчас нет."}
        if not title_query:
            return {
                "action": "clarify",
                "pending_action": "delete_task",
                "payload": {},
                "candidates": [self._task_to_ai_dict(task) for task in active_tasks[:7]],
                "answer": self._build_candidates_answer(active_tasks[:7], "Какую задачу удалить?"),
            }
        matches = self.find_tasks_by_title(title_query)
        if not matches:
            return {"action": "clarify", "answer": "Не нашел задачу с таким названием. Могу показать активные задачи для выбора."}
        if len(matches) > 1:
            return {
                "action": "clarify",
                "pending_action": "delete_task",
                "payload": {},
                "candidates": [self._task_to_ai_dict(task) for task in matches[:7]],
                "answer": self._build_candidates_answer(matches[:7], "Какую задачу удалить?"),
            }

        task = matches[0]
        self.delete_task(task.id)
        return {"deleted": True, "task_id": task.id, "answer": f"Готово, удалил задачу «{task.title}»."}

    def mark_task_done_from_ai(self, payload: dict):
        task_id = payload.get("task_id")
        if task_id:
            task = self.get_task(int(task_id))
            if not task:
                return {"action": "clarify", "answer": "Не нашел такую задачу."}
            self.mark_task_done(task.id)
            return {"completed": True, "task_id": task.id, "answer": f"Готово, отметил «{task.title}» как выполненную."}

        title_query = payload.get("title_query", "")
        active_tasks = self.get_tasks()
        if not active_tasks:
            return {"action": "clarify", "answer": "Активных задач сейчас нет."}
        if not title_query:
            return {
                "action": "clarify",
                "pending_action": "mark_as_done",
                "payload": {},
                "candidates": [self._task_to_ai_dict(task) for task in active_tasks[:7]],
                "answer": self._build_candidates_answer(active_tasks[:7], "Какую задачу отметить выполненной?"),
            }
        matches = self.find_tasks_by_title(title_query)
        if not matches:
            return {"action": "clarify", "answer": "Не нашел задачу с таким названием. Могу показать активные задачи для выбора."}
        if len(matches) > 1:
            return {
                "action": "clarify",
                "pending_action": "mark_as_done",
                "payload": {},
                "candidates": [self._task_to_ai_dict(task) for task in matches[:7]],
                "answer": self._build_candidates_answer(matches[:7], "Какую задачу отметить выполненной?"),
            }

        task = matches[0]
        self.mark_task_done(task.id)
        return {"completed": True, "task_id": task.id, "answer": f"Готово, отметил «{task.title}» как выполненную."}

    def update_task_from_ai(self, payload: dict):
        task_id = payload.get("task_id")
        task = self.get_task(int(task_id)) if task_id else None
        if task is None:
            title_query = payload.get("title_query", "")
            active_tasks = self.get_tasks()
            if not active_tasks:
                return {"action": "clarify", "answer": "Активных задач сейчас нет."}
            if not title_query:
                update_payload = dict(payload)
                update_payload.pop("task_id", None)
                return {
                    "action": "clarify",
                    "pending_action": "update_task",
                    "payload": update_payload,
                    "candidates": [self._task_to_ai_dict(item) for item in active_tasks[:7]],
                    "answer": self._build_candidates_answer(active_tasks[:7], "Какую задачу изменить?"),
                }
            matches = self.find_tasks_by_title(title_query)
            if not matches:
                return {"action": "clarify", "answer": "Не нашел задачу для изменения. Могу показать активные задачи для выбора."}
            if len(matches) > 1:
                update_payload = dict(payload)
                update_payload.pop("task_id", None)
                return {
                    "action": "clarify",
                    "pending_action": "update_task",
                    "payload": update_payload,
                    "candidates": [self._task_to_ai_dict(item) for item in matches[:7]],
                    "answer": self._build_candidates_answer(matches[:7], "Какую задачу изменить?"),
                }
            task = matches[0]

        editable_fields = {"title", "description", "category", "due_date", "recurrence", "priority", "clear_due_date"}
        if not any(field in payload for field in editable_fields):
            return {
                "action": "clarify",
                "pending_action": "update_task",
                "payload": {"task_id": task.id},
                "answer": f"Что изменить в задаче «{task.title}»?",
            }

        task_data = {
            "title": str(payload.get("title", task.title)).strip() or task.title,
            "description": str(payload.get("description", task.description)).strip(),
            "category": str(payload.get("category", task.category)).strip().lower(),
            "due_date": task.due_date,
            "due_time": task.due_time,
            "recurrence": str(payload.get("recurrence", task.recurrence)).strip().lower(),
            "priority": self._priority_from_ai(payload.get("priority"), task.priority),
            "status": task.status,
        }
        if payload.get("clear_due_date"):
            task_data["due_date"] = ""
            task_data["due_time"] = ""
        if payload.get("due_date"):
            normalized_due = str(payload["due_date"]).replace("T", " ").strip()
            if " " in normalized_due:
                task_data["due_date"], task_data["due_time"] = normalized_due.split(" ", 1)
                task_data["due_time"] = task_data["due_time"][:5]
            else:
                task_data["due_date"] = normalized_due
                task_data["due_time"] = ""

        self.save_task(task_data, task.id)
        return {"updated": True, "task_id": task.id, "answer": f"Готово, обновил задачу «{task.title}»."}

    def list_tasks_for_ai(self, filters: dict):
        tasks = self.get_tasks()
        category = (filters.get("category") or "").strip().lower()
        status = (filters.get("status") or "").strip().lower()
        title_query = (filters.get("title_query") or "").strip().lower()
        start_date = (filters.get("start_date") or "").strip()
        end_date = (filters.get("end_date") or "").strip()
        view = (filters.get("view") or "").strip().lower()

        result = []
        for task in tasks:
            if category and task.category.lower() != category:
                continue
            if status and task.status.lower() != status:
                continue
            if title_query and title_query not in task.title.lower():
                continue
            if start_date and task.due_date and task.due_date < start_date:
                continue
            if end_date and task.due_date and task.due_date > end_date:
                continue
            result.append(task)

        if view == "actual" and result:
            def sort_key(task):
                priority_score = {"высокий": 0, "средний": 1, "низкий": 2}.get(task.priority, 1)
                status_score = {"просрочена": 0, "активна": 1}.get(task.status, 2)
                due_score = task.due_date or "9999-12-31"
                return (status_score, priority_score, due_score, task.id or 0)

            result = sorted(result, key=sort_key)[:12]

        if not result:
            return {"tasks": [], "answer": "Подходящих задач не нашлось."}

        preview_lines = []
        for task in result[:7]:
            due_at = f"{task.due_date} {task.due_time}".strip()
            preview_lines.append(f"• {task.title} — {task.category}, {due_at or 'без срока'}")

        more_suffix = "" if len(result) <= 7 else f"\nИ еще {len(result) - 7} шт."
        return {
            "tasks": [self._task_to_ai_dict(task) for task in result],
            "answer": "Вот что нашел:\n" + "\n".join(preview_lines) + more_suffix,
        }

    def get_statistics_for_ai(self):
        self.update_overdue_tasks()
        s = self.database.get_stats()
        return {
            "total": s["total"],
            "active": s["active"],
            "completed": s["completed"],
            "overdue": s["overdue"],
            "answer": (
                f"Сейчас у тебя {s['total']} задач: активных {s['active']}, "
                f"выполненных {s['completed']}, просроченных {s['overdue']}."
            ),
        }

    @staticmethod
    def _task_to_ai_dict(task: Task):
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "category": task.category,
            "due_date": f"{task.due_date} {task.due_time}".strip(),
            "recurrence": task.recurrence,
            "priority": task.priority,
            "status": task.status,
        }

    @staticmethod
    def _build_candidates_answer(tasks, intro: str):
        lines = [intro]
        for index, task in enumerate(tasks, start=1):
            due_at = f"{task.due_date} {task.due_time}".strip() or "без срока"
            lines.append(f"{index}. {task.title} ({due_at})")
        lines.append("Можно ответить номером, например: 1")
        return "\n".join(lines)

    @staticmethod
    def _priority_from_ai(value, current_priority: str) -> str:
        if value in (None, ""):
            return current_priority
        mapping = {1: "низкий", 2: "средний", 3: "высокий"}
        try:
            return mapping.get(int(value), current_priority)
        except (TypeError, ValueError):
            return current_priority

    @staticmethod
    def _normalize_search_tokens(value: str):
        endings = (
            "иями",
            "ями",
            "ами",
            "ого",
            "ему",
            "ому",
            "ыми",
            "ими",
            "ую",
            "юю",
            "ой",
            "ей",
            "ий",
            "ый",
            "ая",
            "яя",
            "а",
            "я",
            "у",
            "ю",
            "ы",
            "и",
            "е",
            "о",
        )
        tokens = []
        for raw_token in value.lower().replace("ё", "е").split():
            token = "".join(ch for ch in raw_token if ch.isalnum())
            if len(token) <= 2:
                continue
            for ending in endings:
                if token.endswith(ending) and len(token) - len(ending) >= 4:
                    token = token[: -len(ending)]
                    break
            tokens.append(token)
        return set(tokens)

    @staticmethod
    def calculate_status(due_date_text: str, due_time_text: str, current_status: str) -> str:
        if current_status.strip().lower() == "выполнена":
            return "выполнена"
        if not due_date_text:
            return "активна"
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
        if not task.due_date:
            return "Без срока"

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
        due_date = task_data["due_date"].strip()
        due_time = task_data["due_time"].strip()
        recurrence = task_data["recurrence"].strip().lower()

        if not due_date:
            if due_time:
                raise ValueError("Сначала выберите дату дедлайна.")
            if recurrence != "одноразовая":
                raise ValueError("Для повторяющейся задачи нужно указать дату дедлайна.")
            return

        TaskService.parse_date(due_date)
        if due_time:
            TaskService.parse_time(due_time)
