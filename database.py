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
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_active ON tasks (is_archived, status, due_date)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_archived ON tasks (is_archived, archived_at)"
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

    def update_overdue_statuses(self, now_iso: str):
        """Bulk-update task statuses in SQL — no Python iteration needed."""
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = CASE
                    WHEN due_date = '' THEN 'активна'
                    WHEN (due_date || ' ' || COALESCE(NULLIF(due_time, ''), '23:59')) < ? THEN 'просрочена'
                    ELSE 'активна'
                END,
                updated_at = CURRENT_TIMESTAMP
                WHERE is_archived = 0
                  AND status != 'выполнена'
                  AND status != CASE
                    WHEN due_date = '' THEN 'активна'
                    WHEN (due_date || ' ' || COALESCE(NULLIF(due_time, ''), '23:59')) < ? THEN 'просрочена'
                    ELSE 'активна'
                END
                """,
                (now_iso, now_iso),
            )

    def get_tasks_filtered(self, status_filter: str, category_filter: str, search_text: str):
        """Return active tasks with optional SQL-level filtering."""
        conditions = ["is_archived = 0"]
        params: list = []

        if status_filter and status_filter != "все":
            conditions.append("LOWER(status) = ?")
            params.append(status_filter.lower())

        if category_filter and category_filter != "все":
            conditions.append("LOWER(category) = ?")
            params.append(category_filter.lower())

        where = " AND ".join(conditions)
        query = f"""
            SELECT * FROM tasks
            WHERE {where}
            ORDER BY
                CASE WHEN due_date = '' THEN 1 ELSE 0 END,
                due_date ASC,
                CASE WHEN due_time = '' THEN 1 ELSE 0 END,
                due_time ASC,
                priority DESC,
                id DESC
        """
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        tasks = [self._row_to_task(row) for row in rows]

        if search_text:
            needle = search_text.lower()
            tasks = [t for t in tasks if needle in t.title.lower()]

        return tasks

    def get_stats(self) -> dict:
        """Return task counts via SQL aggregation."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    SUM(CASE WHEN is_archived = 0 THEN 1 ELSE 0 END) AS total,
                    SUM(CASE WHEN status = 'активна'   AND is_archived = 0 THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN status = 'выполнена' AND is_archived = 1 THEN 1 ELSE 0 END) AS completed,
                    SUM(CASE WHEN status = 'просрочена' AND is_archived = 0 THEN 1 ELSE 0 END) AS overdue
                FROM tasks
                """
            ).fetchone()
        return {
            "total": rows["total"] or 0,
            "active": rows["active"] or 0,
            "completed": rows["completed"] or 0,
            "overdue": rows["overdue"] or 0,
        }

    def clear_archived_tasks(self):
        with self._connect() as connection:
            connection.execute("DELETE FROM tasks WHERE is_archived = 1")

    def get_task(self, task_id: int):
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def get_all_tasks(self):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM tasks
                ORDER BY
                    CASE WHEN due_date = '' THEN 1 ELSE 0 END,
                    due_date ASC,
                    CASE WHEN due_time = '' THEN 1 ELSE 0 END,
                    due_time ASC,
                    priority DESC,
                    id DESC
                """
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
            due_time=row["due_time"] or "",
            recurrence=row["recurrence"],
            priority=row["priority"],
            status=row["status"],
            is_archived=row["is_archived"] or 0,
            archived_at=row["archived_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
