import sqlite3
from app.models.db import get_connection


class CrawlTaskRepository:
    @staticmethod
    def init_table():
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_task(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    cron_expr TEXT NOT NULL DEFAULT '0 * * * *',
                    extract_rule TEXT NOT NULL DEFAULT 'title',
                    status INTEGER NOT NULL DEFAULT 1,
                    last_run TEXT,
                    next_run TEXT,
                    create_time TEXT NOT NULL DEFAULT(datetime('now'))
                )
                """
            )
            conn.commit()

    @staticmethod
    def create(task_name, url, cron_expr='0 * * * *', extract_rule='title', status=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO crawl_task(task_name, url, cron_expr, extract_rule, status) VALUES(?, ?, ?, ?, ?)",
                    (task_name, url, cron_expr, extract_rule, status)
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_all(page=1, page_size=10):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM crawl_task ORDER BY create_time DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM crawl_task").fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(task_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM crawl_task WHERE id = ?", (task_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(task_id, **kwargs):
        update_fields = []
        params = []
        allowed = ['task_name', 'url', 'cron_expr', 'extract_rule', 'status', 'last_run', 'next_run']
        for key in allowed:
            if key in kwargs and kwargs[key] is not None:
                update_fields.append(f"{key} = ?")
                params.append(kwargs[key])
        if not update_fields:
            return False
        params.append(task_id)
        sql = f"UPDATE crawl_task SET {','.join(update_fields)} WHERE id = ?"
        with get_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
        return True

    @staticmethod
    def delete(task_id):
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM crawl_task WHERE id = ?", (task_id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def get_enabled_tasks():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM crawl_task WHERE status = 1").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def toggle_status(task_id):
        with get_connection() as conn:
            conn.execute("UPDATE crawl_task SET status = 1 - status WHERE id = ?", (task_id,))
            conn.commit()
        return True


class CrawlLogRepository:
    @staticmethod
    def init_table():
        with get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crawl_log(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT DEFAULT 'running',
                    result_summary TEXT,
                    error_msg TEXT,
                    raw_content TEXT,
                    FOREIGN KEY (task_id) REFERENCES crawl_task(id) ON DELETE CASCADE
                )
                """
            )
            conn.commit()

    @staticmethod
    def create(task_id, start_time, status='running'):
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO crawl_log(task_id, start_time, status) VALUES(?, ?, ?)",
                (task_id, start_time, status)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def update(log_id, **kwargs):
        update_fields = []
        params = []
        allowed = ['end_time', 'status', 'result_summary', 'error_msg', 'raw_content']
        for key in allowed:
            if key in kwargs and kwargs[key] is not None:
                update_fields.append(f"{key} = ?")
                params.append(kwargs[key])
        if not update_fields:
            return False
        params.append(log_id)
        sql = f"UPDATE crawl_log SET {','.join(update_fields)} WHERE id = ?"
        with get_connection() as conn:
            conn.execute(sql, params)
            conn.commit()
        return True

    @staticmethod
    def get_all(page=1, page_size=10, task_id=None, status=None, start_date=None, end_date=None):
        offset = (page - 1) * page_size
        conditions = []
        params = []
        if task_id:
            conditions.append("cl.task_id = ?")
            params.append(task_id)
        if status:
            conditions.append("cl.status = ?")
            params.append(status)
        if start_date:
            conditions.append("cl.start_time >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("cl.start_time <= ?")
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT cl.*, ct.task_name FROM crawl_log cl LEFT JOIN crawl_task ct ON cl.task_id = ct.id {where_clause} ORDER BY cl.start_time DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
            count_row = conn.execute(
                f"SELECT COUNT(*) as total FROM crawl_log cl {where_clause}",
                params
            ).fetchone()
        return [dict(row) for row in rows], count_row["total"] if count_row else 0

    @staticmethod
    def get_by_id(log_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT cl.*, ct.task_name, ct.url FROM crawl_log cl LEFT JOIN crawl_task ct ON cl.task_id = ct.id WHERE cl.id = ?",
                (log_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def delete_by_task(task_id):
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM crawl_log WHERE task_id = ?", (task_id,))
            conn.commit()
        return cursor.rowcount
