"""
数据库管理模块
---------------
负责所有 SQLite 数据库操作：建表、增删改查。
"""

import sqlite3
import threading
from datetime import datetime, date
from src.config import DB_PATH


class DatabaseManager:
    """数据库管理器，封装所有数据库操作。"""

    def __init__(self, db_path: str = DB_PATH):
        """
        初始化数据库管理器。

        参数:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._lock = threading.Lock()  # 线程锁，防止并发写入冲突
        self._init_tables()

    # ================================================================
    # 内部工具方法
    # ================================================================

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接（每次调用创建新连接，线程安全）。"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 让查询结果可以用字典方式访问
        conn.execute("PRAGMA journal_mode=WAL")  # WAL 模式提高并发性能
        return conn

    def _init_tables(self):
        """初始化数据库表（如果不存在则创建）。"""
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            # 活动记录表：记录每次窗口切换
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    window_title TEXT DEFAULT '',
                    category TEXT DEFAULT 'neutral',
                    start_time DATETIME NOT NULL,
                    end_time DATETIME,
                    duration INTEGER DEFAULT 0,
                    date TEXT NOT NULL
                )
            """)

            # 黑名单表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL UNIQUE,
                    display_name TEXT DEFAULT '',
                    category TEXT DEFAULT 'entertainment'
                )
            """)

            # 白名单表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL UNIQUE,
                    display_name TEXT DEFAULT ''
                )
            """)

            # 专注记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS focus_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time DATETIME NOT NULL,
                    planned_duration INTEGER NOT NULL,
                    actual_duration INTEGER DEFAULT 0,
                    interruptions INTEGER DEFAULT 0,
                    completed INTEGER DEFAULT 0
                )
            """)

            # 每日限额表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_limits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL UNIQUE,
                    display_name TEXT DEFAULT '',
                    limit_minutes INTEGER NOT NULL,
                    enabled INTEGER DEFAULT 1
                )
            """)

            # 设置表（键值对）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            conn.commit()
            conn.close()

    # ================================================================
    # 活动记录相关操作
    # ================================================================

    def add_activity(self, process_name: str, window_title: str,
                     category: str = "neutral") -> int:
        """
        新增一条活动记录（开始使用某个程序）。

        返回: 新记录的 ID
        """
        now = datetime.now()
        today = date.today().isoformat()

        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (process_name, window_title, category,
                                          start_time, date)
                VALUES (?, ?, ?, ?, ?)
            """, (process_name, window_title, category, now, today))
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()

        return record_id

    def end_activity(self, record_id: int):
        """
        结束一条活动记录（用户切换到了其他窗口）。

        参数:
            record_id: 要结束的活动记录 ID
        """
        now = datetime.now()

        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()

            # 计算持续时长
            cursor.execute(
                "SELECT start_time FROM activity_log WHERE id = ?",
                (record_id,)
            )
            row = cursor.fetchone()
            if row:
                start_time = datetime.fromisoformat(row["start_time"])
                duration = int((now - start_time).total_seconds())

                # 只记录超过最短时长的记录
                from src.config import MIN_DURATION
                if duration >= MIN_DURATION:
                    cursor.execute("""
                        UPDATE activity_log
                        SET end_time = ?, duration = ?
                        WHERE id = ?
                    """, (now, duration, record_id))
                else:
                    # 太短的记录直接删除
                    cursor.execute(
                        "DELETE FROM activity_log WHERE id = ?",
                        (record_id,)
                    )

            conn.commit()
            conn.close()

    def get_today_activities(self):
        """获取今日所有活动记录。"""
        today = date.today().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_log
            WHERE date = ? AND duration > 0
            ORDER BY start_time DESC
        """, (today,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_today_total_seconds(self) -> int:
        """获取今日总使用时长（秒）。"""
        today = date.today().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) as total
            FROM activity_log
            WHERE date = ? AND duration > 0
        """, (today,))
        total = cursor.fetchone()["total"]
        conn.close()
        return total

    def get_top_processes(self, date_str: str = None, limit: int = 5):
        """获取指定日期使用时长最长的程序 Top N。"""
        if date_str is None:
            date_str = date.today().isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT process_name,
                   COALESCE(SUM(duration), 0) as total_seconds,
                   COUNT(*) as session_count
            FROM activity_log
            WHERE date = ? AND duration > 0
            GROUP BY process_name
            ORDER BY total_seconds DESC
            LIMIT ?
        """, (date_str, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_activities_by_date(self, date_str: str):
        """获取指定日期的活动记录。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM activity_log
            WHERE date = ? AND duration > 0
            ORDER BY start_time DESC
        """, (date_str,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_weekly_stats(self, start_date_str: str) -> list:
        """获取从 start_date 起 7 天每天的 total_seconds，返回 [{date, total_seconds}]。"""
        from datetime import timedelta
        start = date.fromisoformat(start_date_str)
        dates = [(start + timedelta(days=i)).isoformat() for i in range(7)]

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, COALESCE(SUM(duration), 0) as total_seconds
            FROM activity_log
            WHERE date BETWEEN ? AND ? AND duration > 0
            GROUP BY date
        """, (dates[0], dates[-1]))
        rows = cursor.fetchall()
        conn.close()

        result_map = {row["date"]: row["total_seconds"] for row in rows}
        return [{"date": d, "total_seconds": result_map.get(d, 0)} for d in dates]

    def get_monthly_stats(self, year: int, month: int) -> list:
        """获取某月每天的 total_seconds，返回 [{date, total_seconds}]。"""
        import calendar
        from datetime import timedelta
        days_in_month = calendar.monthrange(year, month)[1]
        dates = [date(year, month, day).isoformat()
                 for day in range(1, days_in_month + 1)]

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, COALESCE(SUM(duration), 0) as total_seconds
            FROM activity_log
            WHERE date BETWEEN ? AND ? AND duration > 0
            GROUP BY date
        """, (dates[0], dates[-1]))
        rows = cursor.fetchall()
        conn.close()

        result_map = {row["date"]: row["total_seconds"] for row in rows}
        return [{"date": d, "total_seconds": result_map.get(d, 0)} for d in dates]

    def get_category_breakdown(self, date_str: str = None) -> list:
        """按 category 统计时长，返回 [{category, total_seconds}]。"""
        if date_str is None:
            date_str = date.today().isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COALESCE(SUM(duration), 0) as total_seconds
            FROM activity_log
            WHERE date = ? AND duration > 0
            GROUP BY category
        """, (date_str,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_streak_days(self) -> int:
        """获取连续使用天数（从今天往前连续有活动记录的天数）。"""
        from datetime import timedelta
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT date FROM activity_log
            WHERE duration > 0
            ORDER BY date DESC
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return 0

        existing_dates = {row["date"] for row in rows}
        today = date.today()
        streak = 0
        for i in range(len(existing_dates) + 1):
            check_date = (today - timedelta(days=i)).isoformat()
            if check_date in existing_dates:
                streak += 1
            else:
                break
        return streak

    def get_daily_usage_for_process(self, process_name: str, date_str: str = None) -> int:
        """
        获取某程序在指定日期的总使用秒数。

        参数:
            process_name: 进程名
            date_str: 日期字符串，默认今天
        返回: 总秒数
        """
        if date_str is None:
            date_str = date.today().isoformat()

        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(duration), 0) as total
            FROM activity_log
            WHERE process_name = ? AND date = ? AND duration > 0
        """, (process_name, date_str))
        total = cursor.fetchone()["total"]
        conn.close()
        return total

    def delete_activity(self, record_id: int):
        """删除单条活动记录。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM activity_log WHERE id = ?", (record_id,))
            conn.commit()
            conn.close()

    def delete_activities_by_date(self, date_str: str):
        """删除指定日期的所有活动记录。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM activity_log WHERE date = ?", (date_str,))
            conn.commit()
            conn.close()

    def delete_all_activities(self):
        """清空所有活动记录。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM activity_log")
            conn.commit()
            conn.close()

    def cleanup_old_data(self, retention_days: int = 90):
        """清理超过保留天数的旧数据。"""
        from datetime import timedelta
        cutoff = (date.today() - timedelta(days=retention_days)).isoformat()

        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM activity_log WHERE date < ?", (cutoff,)
            )
            conn.commit()
            conn.close()

    # ================================================================
    # 黑名单相关操作
    # ================================================================

    def get_blacklist(self) -> list:
        """获取所有黑名单条目。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blacklist ORDER BY display_name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_to_blacklist(self, process_name: str, display_name: str = "",
                         category: str = "entertainment"):
        """添加程序到黑名单。"""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO blacklist (process_name, display_name, category) VALUES (?, ?, ?)",
                    (process_name, display_name, category)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                pass  # 已存在则忽略
            finally:
                conn.close()

    def remove_from_blacklist(self, process_name: str):
        """从黑名单中移除程序。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM blacklist WHERE process_name = ?",
                (process_name,)
            )
            conn.commit()
            conn.close()

    def is_blacklisted(self, process_name: str) -> bool:
        """检查程序是否在黑名单中。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM blacklist WHERE process_name = ?",
            (process_name,)
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result

    # ================================================================
    # 白名单相关操作
    # ================================================================

    def get_whitelist(self) -> list:
        """获取所有白名单条目。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM whitelist ORDER BY display_name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_to_whitelist(self, process_name: str, display_name: str = ""):
        """添加程序到白名单。"""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO whitelist (process_name, display_name) VALUES (?, ?)",
                    (process_name, display_name)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                pass
            finally:
                conn.close()

    def remove_from_whitelist(self, process_name: str):
        """从白名单中移除程序。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM whitelist WHERE process_name = ?",
                (process_name,)
            )
            conn.commit()
            conn.close()

    def is_whitelisted(self, process_name: str) -> bool:
        """检查程序是否在白名单中。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM whitelist WHERE process_name = ?",
            (process_name,)
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result

    # ================================================================
    # 专注记录相关操作
    # ================================================================

    def add_focus_session(self, planned_duration: int) -> int:
        """新增一次专注记录，返回记录 ID。"""
        now = datetime.now()
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO focus_sessions (start_time, planned_duration)
                VALUES (?, ?)
            """, (now, planned_duration))
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
        return session_id

    def end_focus_session(self, session_id: int, interruptions: int = 0,
                          completed: bool = True):
        """结束一次专注记录。"""
        now = datetime.now()
        with self._lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT start_time FROM focus_sessions WHERE id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                start_time = datetime.fromisoformat(row["start_time"])
                actual_duration = int((now - start_time).total_seconds())
                cursor.execute("""
                    UPDATE focus_sessions
                    SET actual_duration = ?, interruptions = ?, completed = ?
                    WHERE id = ?
                """, (actual_duration, interruptions, int(completed), session_id))
            conn.commit()
            conn.close()

    def get_focus_sessions(self, limit: int = 50) -> list:
        """获取最近的专注记录。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM focus_sessions
            ORDER BY start_time DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_focus_count_today(self) -> int:
        """获取今天完成的专注次数。"""
        today = date.today().isoformat()
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM focus_sessions
            WHERE date(start_time) = ? AND completed = 1
        """, (today,))
        result = cursor.fetchone()["cnt"]
        conn.close()
        return result

    def get_total_focus_hours(self) -> float:
        """获取累计专注总小时数。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(actual_duration), 0) as total_seconds
            FROM focus_sessions
            WHERE completed = 1
        """)
        total_seconds = cursor.fetchone()["total_seconds"]
        conn.close()
        return total_seconds / 3600.0

    # ================================================================
    # 每日限额相关操作
    # ================================================================

    def get_daily_limits(self) -> list:
        """获取所有每日限额设置。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM daily_limits ORDER BY display_name")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def set_daily_limit(self, process_name: str, display_name: str,
                        limit_minutes: int):
        """设置或更新某程序的每日限额。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                INSERT INTO daily_limits (process_name, display_name, limit_minutes)
                VALUES (?, ?, ?)
                ON CONFLICT(process_name) DO UPDATE SET
                    display_name = excluded.display_name,
                    limit_minutes = excluded.limit_minutes
            """, (process_name, display_name, limit_minutes))
            conn.commit()
            conn.close()

    def remove_daily_limit(self, process_name: str):
        """移除某程序的每日限额。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM daily_limits WHERE process_name = ?",
                (process_name,)
            )
            conn.commit()
            conn.close()

    # ================================================================
    # 设置相关操作
    # ================================================================

    def get_setting(self, key: str, default: str = "") -> str:
        """获取设置值。"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        conn.close()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """保存设置值。"""
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            conn.commit()
            conn.close()

    def mark_onboarding_done(self):
        """标记新手引导已完成。"""
        self.set_setting("onboarding_done", "1")

    def is_onboarding_done(self) -> bool:
        """检查新手引导是否已完成。"""
        return self.get_setting("onboarding_done") == "1"
