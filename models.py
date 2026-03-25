from dataclasses import dataclass
from typing import Optional


CATEGORIES = ["лекарства", "платежи", "бытовые дела", "подписки", "другое"]
RECURRENCE_OPTIONS = ["одноразовая", "ежедневно", "еженедельно", "ежемесячно"]
PRIORITY_OPTIONS = ["низкий", "средний", "высокий"]
STATUS_OPTIONS = ["активна", "выполнена", "просрочена"]


@dataclass
class Task:
    """Task entity used in the application."""

    id: Optional[int]
    title: str
    description: str
    category: str
    due_date: str
    due_time: str
    recurrence: str
    priority: str
    status: str
    is_archived: int = 0
    archived_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
