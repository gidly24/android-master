import sqlite3
from pathlib import Path

from models import Task


class DatabaseManager:
    """SQLite wrapper with basic CRUD operations."""

    def __init__(self, db_path: Path):
        self.was_created = not db_path.exists()
        self.db_path = str(db_path)
        self._create_schema()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    due_time TEXT NOT NULL DEFAULT '23:59',
                    recurrence TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_archived INTEGER NOT NULL DEFAULT 0,
                    archived_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "due_time" not in columns:
                connection.execute(
                    "ALTER TABLE tasks ADD COLUMN due_time TEXT NOT NULL DEFAULT '23:59'"
                )
            if "is_archived" not in columns:
                connection.execute(
                    "ALTER TABLE tasks ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0"
                )
            if "archived_at" not in columns:
                connection.execute(
                    "ALTER TABLE tasks ADD COLUMN archived_at TEXT"
                )

    def get_app_state(self, key: str):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM app_state WHERE key = ?",
                (key,),
            ).fetchone()
        return row["value"] if row else None

    def set_app_state(self, key: str, value: str):
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO app_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def create_task(self, task: Task) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (
                    title, description, category, due_date, due_time, recurrence, priority, status,
                    is_archived, archived_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    task.title,
                    task.description,
                    task.category,
                    task.due_date,
                    task.due_time,
                    task.recurrence,
                    task.priority,
                    task.status,
                    task.is_archived,
                    task.archived_at,
                ),
            )
            return cursor.lastrowid

    def update_task(self, task: Task):
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, category = ?, due_date = ?, due_time = ?, recurrence = ?,
                    priority = ?, status = ?, is_archived = ?, archived_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    task.title,
                    task.description,
                    task.category,
                    task.due_date,
                    task.due_time,
                    task.recurrence,
                    task.priority,
                    task.status,
                    task.is_archived,
                    task.archived_at,
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
                "SELECT * FROM tasks ORDER BY due_date ASC, due_time ASC, priority DESC, id DESC"
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def get_archived_tasks(self):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM tasks
                WHERE is_archived = 1
                ORDER BY archived_at DESC, updated_at DESC, id DESC
                """
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
            due_time=row["due_time"] or "23:59",
            recurrence=row["recurrence"],
            priority=row["priority"],
            status=row["status"],
            is_archived=row["is_archived"] or 0,
            archived_at=row["archived_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
