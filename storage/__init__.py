import sqlite3
from typing import Optional, List
from datetime import date, datetime
from models import User, Plan, Task
from storage.base import StorageInterface


class SQLiteStorage(StorageInterface):
    def __init__(self, db_path: str):
        if db_path.startswith("sqlite+aiosqlite:///"):
            db_path = db_path.replace("sqlite+aiosqlite:///", "")

        self.db_path = db_path
        self._conn = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                timezone TEXT DEFAULT 'UTC'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                deadline TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                deadline TEXT NOT NULL,
                is_done INTEGER DEFAULT 0,
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plan_tasks (
                plan_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                PRIMARY KEY (plan_id, task_id),
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                deadline TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                delta_seconds INTEGER NOT NULL,
                sent INTEGER DEFAULT 0,
                PRIMARY KEY (task_id, reminder_type)
            )
        """)

        conn.commit()

    def get_user(self, user_id: int) -> Optional[User]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return User(user_id=row["user_id"], username=row["username"], timezone=row["timezone"])

    def save_user(self, user_id: int, username: Optional[str]):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, timezone) VALUES (?, ?, 'UTC')",
            (user_id, username),
        )
        conn.commit()

    def create_plan(self, user_id: int, subject: str, deadline: Optional[date]) -> Plan:
        conn = self._get_conn()
        cursor = conn.cursor()
        deadline_str = deadline.isoformat() if deadline else None
        cursor.execute(
            "INSERT INTO plans (user_id, subject, deadline) VALUES (?, ?, ?)",
            (user_id, subject, deadline_str),
        )
        conn.commit()
        plan_id = cursor.lastrowid
        return Plan(plan_id=plan_id, user_id=user_id, subject=subject, deadline=deadline, tasks=[])

    def update_plan_deadline(self, plan_id: int, deadline: Optional[date]) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        deadline_str = deadline.isoformat() if deadline else None
        cursor.execute("UPDATE plans SET deadline = ? WHERE plan_id = ?", (deadline_str, plan_id))
        conn.commit()
        return cursor.rowcount > 0

    def get_plan(self, plan_id: int) -> Optional[Plan]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plans WHERE plan_id = ?", (plan_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        deadline = datetime.fromisoformat(row["deadline"]).date() if row["deadline"] else None
        task_ids = self._get_plan_task_ids(plan_id)
        return Plan(
            plan_id=row["plan_id"],
            user_id=row["user_id"],
            subject=row["subject"],
            deadline=deadline,
            tasks=task_ids,
        )

    def _get_plan_task_ids(self, plan_id: int) -> List[int]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT task_id FROM plan_tasks WHERE plan_id = ?", (plan_id,))
        return [row["task_id"] for row in cursor.fetchall()]

    def get_user_plans(self, user_id: int) -> List[Plan]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM plans WHERE user_id = ?", (user_id,))
        plans = []
        for row in cursor.fetchall():
            deadline = datetime.fromisoformat(row["deadline"]).date() if row["deadline"] else None
            task_ids = self._get_plan_task_ids(row["plan_id"])
            plans.append(
                Plan(
                    plan_id=row["plan_id"],
                    user_id=row["user_id"],
                    subject=row["subject"],
                    deadline=deadline,
                    tasks=task_ids,
                )
            )
        return plans

    def get_plan_by_subject(self, user_id: int, subject: str) -> Optional[Plan]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM plans WHERE user_id = ? AND LOWER(subject) = LOWER(?)",
            (user_id, subject),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        deadline = datetime.fromisoformat(row["deadline"]).date() if row["deadline"] else None
        task_ids = self._get_plan_task_ids(row["plan_id"])
        return Plan(
            plan_id=row["plan_id"],
            user_id=row["user_id"],
            subject=row["subject"],
            deadline=deadline,
            tasks=task_ids,
        )

    def get_task_by_title(self, plan_id: int, title: str) -> Optional[Task]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE plan_id = ? AND LOWER(title) = LOWER(?)", (plan_id, title)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        deadline = datetime.fromisoformat(row["deadline"]).date()
        return Task(
            task_id=row["task_id"],
            plan_id=row["plan_id"],
            title=row["title"],
            deadline=deadline,
            is_done=bool(row["is_done"]),
        )

    def delete_plan(self, plan_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT task_id FROM plan_tasks WHERE plan_id = ?", (plan_id,))
        task_ids = [row["task_id"] for row in cursor.fetchall()]

        for task_id in task_ids:
            cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))

        cursor.execute("DELETE FROM plan_tasks WHERE plan_id = ?", (plan_id,))
        cursor.execute("DELETE FROM plans WHERE plan_id = ?", (plan_id,))
        conn.commit()

        return cursor.rowcount > 0

    def create_task(self, plan_id: int, title: str, deadline: date) -> Task:
        conn = self._get_conn()
        cursor = conn.cursor()
        deadline_str = deadline.isoformat()
        cursor.execute(
            "INSERT INTO tasks (plan_id, title, deadline, is_done) VALUES (?, ?, ?, 0)",
            (plan_id, title, deadline_str),
        )
        task_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO plan_tasks (plan_id, task_id) VALUES (?, ?)", (plan_id, task_id)
        )
        conn.commit()

        return Task(task_id=task_id, plan_id=plan_id, title=title, deadline=deadline, is_done=False)

    def get_task(self, task_id: int) -> Optional[Task]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        deadline = datetime.fromisoformat(row["deadline"]).date()
        return Task(
            task_id=row["task_id"],
            plan_id=row["plan_id"],
            title=row["title"],
            deadline=deadline,
            is_done=bool(row["is_done"]),
        )

    def get_tasks_by_plan(self, plan_id: int) -> List[Task]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE plan_id = ?", (plan_id,))
        tasks = []
        for row in cursor.fetchall():
            deadline = datetime.fromisoformat(row["deadline"]).date()
            tasks.append(
                Task(
                    task_id=row["task_id"],
                    plan_id=row["plan_id"],
                    title=row["title"],
                    deadline=deadline,
                    is_done=bool(row["is_done"]),
                )
            )
        return tasks

    def update_task(self, task: Task) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        deadline_str = task.deadline.isoformat() if task.deadline else None
        cursor.execute(
            "UPDATE tasks SET title = ?, deadline = ?, is_done = ? WHERE task_id = ?",
            (task.title, deadline_str, int(task.is_done), task.task_id),
        )
        conn.commit()
        return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
        cursor.execute("DELETE FROM plan_tasks WHERE task_id = ?", (task_id,))
        cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0

    def get_all_user_tasks(self, user_id: int) -> List[Task]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT t.* FROM tasks t
            JOIN plans p ON t.plan_id = p.plan_id
            WHERE p.user_id = ?
        """,
            (user_id,),
        )
        tasks = []
        for row in cursor.fetchall():
            deadline = datetime.fromisoformat(row["deadline"]).date()
            tasks.append(
                Task(
                    task_id=row["task_id"],
                    plan_id=row["plan_id"],
                    title=row["title"],
                    deadline=deadline,
                    is_done=bool(row["is_done"]),
                )
            )
        return tasks

    def save_reminder(
        self,
        task_id: int,
        user_id: int,
        title: str,
        deadline: date,
        reminder_type: str,
        delta_seconds: int,
    ):
        conn = self._get_conn()
        cursor = conn.cursor()
        deadline_str = deadline.isoformat() if hasattr(deadline, "isoformat") else deadline
        cursor.execute(
            """
            INSERT OR REPLACE INTO reminders (task_id, user_id, title, deadline, reminder_type, delta_seconds, sent)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
            (task_id, user_id, title, deadline_str, reminder_type, delta_seconds),
        )
        conn.commit()

    def delete_reminders_for_task(self, task_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
        conn.commit()

    def get_all_reminders(self) -> List[dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reminders WHERE sent = 0")
        reminders = []
        for row in cursor.fetchall():
            deadline = row["deadline"]
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline).date()
            reminders.append(
                {
                    "task_id": row["task_id"],
                    "user_id": row["user_id"],
                    "title": row["title"],
                    "deadline": deadline,
                    "reminder_type": row["reminder_type"],
                    "delta_seconds": row["delta_seconds"],
                    "key": f"{row['task_id']}_{row['reminder_type']}",
                }
            )
        return reminders

    def mark_reminder_sent(self, task_id: int, reminder_type: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE reminders SET sent = 1 WHERE task_id = ? AND reminder_type = ?",
            (task_id, reminder_type),
        )
        conn.commit()


def _get_storage():
    from config import config

    db_path = config.DATABASE_URL
    return SQLiteStorage(db_path)


storage = _get_storage()
