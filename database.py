import sqlite3
from pathlib import Path

from models import Task


class DatabaseManager:
    """SQLite wrapper with basic CRUD operations."""

    def __init__(self, db_path: Path):
        self.db_path = str(db_path)
        self._create_table()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_table(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    recurrence TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def create_task(self, task: Task) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (
                    title, description, category, due_date, recurrence, priority, status, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    task.title,
                    task.description,
                    task.category,
                    task.due_date,
                    task.recurrence,
                    task.priority,
                    task.status,
                ),
            )
            return cursor.lastrowid

    def update_task(self, task: Task):
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, category = ?, due_date = ?, recurrence = ?,
                    priority = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    task.title,
                    task.description,
                    task.category,
                    task.due_date,
                    task.recurrence,
                    task.priority,
                    task.status,
                    task.id,
                ),
            )

    def delete_task(self, task_id: int):
        with self._connect() as connection:
            connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def get_task(self, task_id: int):
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def get_all_tasks(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tasks ORDER BY due_date ASC, priority DESC, id DESC"
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def count_tasks(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS amount FROM tasks").fetchone()
        return int(row["amount"])

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            category=row["category"],
            due_date=row["due_date"],
            recurrence=row["recurrence"],
            priority=row["priority"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
