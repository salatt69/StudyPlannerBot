import aiosqlite
from typing import Optional, List
from datetime import date, datetime
from models import User, Plan, Task
from storage.base import StorageInterface


class SQLiteStorage(StorageInterface):
    """SQLite storage implementation."""

    def __init__(self, db_path: str):
        """Initializes the storage.

        Args:
            db_path: Path to the database file.
        """
        if db_path.startswith("sqlite+aiosqlite:///"):
            db_path = db_path.replace("sqlite+aiosqlite:///", "")

        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def _get_conn(self) -> aiosqlite.Connection:
        """Gets a connection to the database.

        Returns:
            Database connection.
        """
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row
            await self._init_db()
        return self._conn

    async def _init_db(self):
        """Initializes the database structure."""
        conn = self._conn
        cursor = await conn.cursor()

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                timezone TEXT DEFAULT 'UTC'
            )
            """
        )

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                deadline TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                deadline TEXT NOT NULL,
                is_done INTEGER DEFAULT 0,
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
            )
            """
        )

        await cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_tasks (
                plan_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                PRIMARY KEY (plan_id, task_id),
                FOREIGN KEY (plan_id) REFERENCES plans(plan_id),
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
            """
        )

        await cursor.execute(
            """
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
            """
        )

        await conn.commit()

    async def get_user(self, user_id: int) -> Optional[User]:
        """Gets a user by ID.

        Args:
            user_id: User ID.

        Returns:
            User object or None.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return User(
            user_id=row["user_id"],
            username=row["username"],
            timezone=row["timezone"],
        )

    async def save_user(self, user_id: int, username: Optional[str]):
        """Saves or updates a user.

        Args:
            user_id: User ID.
            username: Username.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, timezone) "
            "VALUES (?, ?, 'UTC')",
            (user_id, username),
        )
        await conn.commit()

    async def create_plan(
        self, user_id: int, subject: str, deadline: Optional[date]
    ) -> Plan:
        """Creates a new plan.

        Args:
            user_id: User ID.
            subject: Subject name.
            deadline: Plan deadline.

        Returns:
            The created plan.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        deadline_str = deadline.isoformat() if deadline else None
        try:
            await cursor.execute(
                "INSERT INTO plans (user_id, subject, deadline) "
                "VALUES (?, ?, ?)",
                (user_id, subject, deadline_str),
            )
            await conn.commit()
            plan_id = cursor.lastrowid
        except Exception as e:
            await conn.rollback()
            raise e
        return Plan(
            plan_id=plan_id,
            user_id=user_id,
            subject=subject,
            deadline=deadline,
            tasks=[],
        )

    async def update_plan_deadline(
        self, plan_id: int, deadline: Optional[date]
    ) -> bool:
        """Updates the plan deadline.

        Args:
            plan_id: Plan ID.
            deadline: New deadline.

        Returns:
            True if updated.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        deadline_str = deadline.isoformat() if deadline else None
        await cursor.execute(
            "UPDATE plans SET deadline = ? WHERE plan_id = ?",
            (deadline_str, plan_id),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def get_plan(self, plan_id: int) -> Optional[Plan]:
        """Gets a plan by ID.

        Args:
            plan_id: Plan ID.

        Returns:
            Plan or None.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        deadline = (
            datetime.fromisoformat(row["deadline"]).date()
            if row["deadline"]
            else None
        )
        task_ids = await self._get_plan_task_ids(plan_id)
        return Plan(
            plan_id=row["plan_id"],
            user_id=row["user_id"],
            subject=row["subject"],
            deadline=deadline,
            tasks=task_ids,
        )

    async def _get_plan_task_ids(self, plan_id: int) -> List[int]:
        """Gets all task IDs for a plan.

        Args:
            plan_id: Plan ID.

        Returns:
            List of task IDs.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT task_id FROM plan_tasks WHERE plan_id = ?", (plan_id,)
        )
        rows = await cursor.fetchall()
        return [row["task_id"] for row in rows]

    async def get_user_plans(self, user_id: int) -> List[Plan]:
        """Gets all plans for a user.

        Args:
            user_id: User ID.

        Returns:
            List of plans.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM plans WHERE user_id = ?", (user_id,)
        )
        plans = []
        for row in await cursor.fetchall():
            deadline = (
                datetime.fromisoformat(row["deadline"]).date()
                if row["deadline"]
                else None
            )
            task_ids = await self._get_plan_task_ids(row["plan_id"])
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

    async def get_plan_by_subject(
        self, user_id: int, subject: str
    ) -> Optional[Plan]:
        """Gets a plan by subject name.

        Args:
            user_id: User ID.
            subject: Subject name.

        Returns:
            Plan or None.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM plans WHERE user_id = ? AND LOWER(subject) "
            "= LOWER(?)",
            (user_id, subject),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        deadline = (
            datetime.fromisoformat(row["deadline"]).date()
            if row["deadline"]
            else None
        )
        task_ids = await self._get_plan_task_ids(row["plan_id"])
        return Plan(
            plan_id=row["plan_id"],
            user_id=row["user_id"],
            subject=row["subject"],
            deadline=deadline,
            tasks=task_ids,
        )

    async def get_task_by_title(
        self, plan_id: int, title: str
    ) -> Optional[Task]:
        """Gets a task by title.

        Args:
            plan_id: Plan ID.
            title: Task title.

        Returns:
            Task or None.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM tasks WHERE plan_id = ? AND LOWER(title) "
            "= LOWER(?)",
            (plan_id, title),
        )
        row = await cursor.fetchone()
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

    async def delete_plan(self, plan_id: int) -> bool:
        """Deletes a plan and all its tasks.

        Args:
            plan_id: Plan ID.

        Returns:
            True if deleted.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT task_id FROM plan_tasks WHERE plan_id = ?", (plan_id,)
        )
        task_ids = [row["task_id"] for row in await cursor.fetchall()]

        for task_id in task_ids:
            await cursor.execute(
                "DELETE FROM reminders WHERE task_id = ?", (task_id,)
            )
            await cursor.execute(
                "DELETE FROM tasks WHERE task_id = ?", (task_id,)
            )

        await cursor.execute(
            "DELETE FROM plan_tasks WHERE plan_id = ?", (plan_id,)
        )
        await cursor.execute("DELETE FROM plans WHERE plan_id = ?", (plan_id,))
        await conn.commit()

        return cursor.rowcount > 0

    async def create_task(
        self, plan_id: int, title: str, deadline: date
    ) -> Task:
        """Creates a new task.

        Args:
            plan_id: Plan ID.
            title: Task title.
            deadline: Deadline.

        Returns:
            The created task.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        deadline_str = deadline.isoformat()
        await cursor.execute(
            "INSERT INTO tasks (plan_id, title, deadline, is_done) "
            "VALUES (?, ?, ?, 0)",
            (plan_id, title, deadline_str),
        )
        task_id = cursor.lastrowid

        await cursor.execute(
            "INSERT INTO plan_tasks (plan_id, task_id) VALUES (?, ?)",
            (plan_id, task_id),
        )
        await conn.commit()

        return Task(
            task_id=task_id,
            plan_id=plan_id,
            title=title,
            deadline=deadline,
            is_done=False,
        )

    async def get_task(self, task_id: int) -> Optional[Task]:
        """Gets a task by ID.

        Args:
            task_id: Task ID.

        Returns:
            Task or None.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        )
        row = await cursor.fetchone()
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

    async def get_tasks_by_plan(self, plan_id: int) -> List[Task]:
        """Gets all tasks for a plan.

        Args:
            plan_id: Plan ID.

        Returns:
            List of tasks.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT * FROM tasks WHERE plan_id = ?", (plan_id,)
        )
        tasks = []
        for row in await cursor.fetchall():
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

    async def update_task(self, task: Task) -> bool:
        """Updates a task.

        Args:
            task: Task object.

        Returns:
            True if updated.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        deadline_str = task.deadline.isoformat() if task.deadline else None
        await cursor.execute(
            "UPDATE tasks SET title = ?, deadline = ?, is_done = ? "
            "WHERE task_id = ?",
            (task.title, deadline_str, int(task.is_done), task.task_id),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def update_task_status(self, task_id: int, is_done: bool) -> bool:
        """Updates the task completion status.

        Args:
            task_id: Task ID.
            is_done: Completion status.

        Returns:
            True if updated.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE tasks SET is_done = ? WHERE task_id = ?",
            (int(is_done), task_id),
        )
        await conn.commit()
        return cursor.rowcount > 0

    async def delete_task(self, task_id: int) -> bool:
        """Deletes a task.

        Args:
            task_id: Task ID.

        Returns:
            True if deleted.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "DELETE FROM reminders WHERE task_id = ?", (task_id,)
        )
        await cursor.execute(
            "DELETE FROM plan_tasks WHERE task_id = ?", (task_id,)
        )
        await cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        await conn.commit()
        return cursor.rowcount > 0

    async def get_all_user_tasks(self, user_id: int) -> List[Task]:
        """Gets all tasks for a user.

        Args:
            user_id: User ID.

        Returns:
            List of tasks.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT t.* FROM tasks t
            JOIN plans p ON t.plan_id = p.plan_id
            WHERE p.user_id = ?
            """,
            (user_id,),
        )
        tasks = []
        for row in await cursor.fetchall():
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

    async def save_reminder(
        self,
        task_id: int,
        user_id: int,
        title: str,
        deadline: date,
        reminder_type: str,
        delta_seconds: int,
    ):
        """Saves a reminder.

        Args:
            task_id: Task ID.
            user_id: User ID.
            title: Task title.
            deadline: Deadline.
            reminder_type: Reminder type.
            delta_seconds: Time until deadline in seconds.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        deadline_str = (
            deadline.isoformat()
            if hasattr(deadline, "isoformat")
            else deadline
        )
        await cursor.execute(
            """
            INSERT OR REPLACE INTO reminders
            (task_id, user_id, title, deadline, reminder_type,
             delta_seconds, sent)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            """,
            (
                task_id,
                user_id,
                title,
                deadline_str,
                reminder_type,
                delta_seconds,
            ),
        )
        await conn.commit()

    async def delete_reminders_for_task(self, task_id: int):
        """Deletes all reminders for a task.

        Args:
            task_id: Task ID.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "DELETE FROM reminders WHERE task_id = ?", (task_id,)
        )
        await conn.commit()

    async def get_all_reminders(self) -> List[dict]:
        """Gets all unsent reminders.

        Returns:
            List of dicts with reminder data.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM reminders WHERE sent = 0")
        reminders = []
        for row in await cursor.fetchall():
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

    async def mark_reminder_sent(self, task_id: int, reminder_type: str):
        """Marks a reminder as sent.

        Args:
            task_id: Task ID.
            reminder_type: Reminder type.
        """
        conn = await self._get_conn()
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE reminders SET sent = 1 WHERE task_id = ? "
            "AND reminder_type = ?",
            (task_id, reminder_type),
        )
        await conn.commit()


def get_storage():
    """Creates a storage instance.

    Returns:
        SQLiteStorage instance.
    """
    from config import config

    db_path = config.DATABASE_URL
    return SQLiteStorage(db_path)


storage = get_storage()