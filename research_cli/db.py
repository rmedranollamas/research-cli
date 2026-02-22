import os
import sqlite3
import threading
import asyncio
from contextlib import contextmanager
from typing import Optional, List, Tuple
from . import config

_db_lock = threading.Lock()
_last_db_path: Optional[str] = None


@contextmanager
def get_db():
    global _last_db_path

    if _last_db_path != config.DB_PATH:
        with _db_lock:
            if _last_db_path != config.DB_PATH:
                _init_db(config.DB_PATH)
                _last_db_path = config.DB_PATH

    conn = sqlite3.connect(config.DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def _init_db(db_path: str):
    db_dir = os.path.dirname(db_path)
    # Set restrictive umask (only user can read/write)
    old_umask = os.umask(0o077)
    try:
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o700, exist_ok=True)
        elif db_dir:
            # Ensure existing directory has correct permissions if it is likely our own app dir
            try:
                st = os.stat(db_dir)
                # Only chmod if we own it and it is not a system directory
                is_owner = hasattr(os, "getuid") and st.st_uid == os.getuid()
                if is_owner and db_dir not in ["/tmp", "/var/tmp", "/"]:
                    os.chmod(db_dir, 0o700)
            except OSError:
                pass

        with sqlite3.connect(db_path) as conn:
            # Ensure database file has correct permissions
            try:
                os.chmod(db_path, 0o600)
            except OSError:
                pass
            _init_db_schema(conn)
    finally:
        os.umask(old_umask)


def _init_db_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interaction_id TEXT UNIQUE, 
            parent_id TEXT,
            query TEXT,
            model TEXT,
            status TEXT,
            report TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_tasks_created_at ON research_tasks (created_at)"
    )
    conn.commit()


def init_db():
    with get_db():
        pass


def save_task(
    query: str,
    model: str,
    interaction_id: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO research_tasks (query, model, interaction_id, status, parent_id) VALUES (?, ?, ?, ?, ?)",
            (query, model, interaction_id, "PENDING", parent_id),
        )
        task_id = cursor.lastrowid
        conn.commit()
        return task_id


async def async_save_task(*args, **kwargs):
    return await asyncio.to_thread(save_task, *args, **kwargs)


def update_task(
    task_id: int,
    status: str,
    report: Optional[str] = None,
    interaction_id: Optional[str] = None,
):
    with get_db() as conn:
        if interaction_id:
            conn.execute(
                "UPDATE research_tasks SET status = ?, report = ?, interaction_id = ? WHERE id = ?",
                (status, report, interaction_id, task_id),
            )
        else:
            conn.execute(
                "UPDATE research_tasks SET status = ?, report = ? WHERE id = ?",
                (status, report, task_id),
            )
        conn.commit()


async def async_update_task(*args, **kwargs):
    return await asyncio.to_thread(update_task, *args, **kwargs)


def get_task(task_id: int) -> Optional[Tuple]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT query, report, status FROM research_tasks WHERE id = ?", (task_id,)
        )
        return cursor.fetchone()


def get_recent_tasks(limit: int) -> List[Tuple]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id, query, status, created_at, interaction_id FROM research_tasks ORDER BY created_at DESC LIMIT {limit}"
        )
        return cursor.fetchall()


async def async_get_task(*args, **kwargs):
    return await asyncio.to_thread(get_task, *args, **kwargs)


async def async_get_recent_tasks(*args, **kwargs):
    return await asyncio.to_thread(get_recent_tasks, *args, **kwargs)
