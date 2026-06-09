"""
活动监控模块
-------------
后台线程定时检测当前活跃窗口，记录程序/网页的使用情况。
"""

import time
import threading
from datetime import datetime, date

# 尝试导入 Windows API
try:
    import win32gui
    import win32process
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    print("⚠️ pywin32 未安装，窗口检测功能不可用。请运行: pip install pywin32")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️ psutil 未安装，进程检测功能不可用。请运行: pip install psutil")

from src.config import CHECK_INTERVAL, MIN_DURATION, IDLE_TIMEOUT


class ActivityMonitor:
    """
    活动监控器。

    在后台线程中运行，定期检测当前活跃窗口，
    记录程序名称、窗口标题和持续时间。
    """

    def __init__(self, db_manager):
        """
        初始化监控器。

        参数:
            db_manager: DatabaseManager 实例，用于存储活动记录
        """
        self.db = db_manager
        self._running = False
        self._thread = None
        self._current_record_id = None  # 当前活动记录的数据库 ID
        self._current_process = None    # 当前进程名
        self._last_active_time = datetime.now()  # 上次用户活动时间

        # 回调函数：当检测到窗口切换时调用
        self.on_switch = None  # 签名: func(process_name, window_title)

        # 回调函数：当限额超时时调用
        self.on_limit_exceeded = None  # 签名: func(process_name, limit_minutes, used_minutes)

    # ================================================================
    # 检测方法
    # ================================================================

    def _get_active_window_info(self) -> tuple:
        """
        获取当前活跃窗口的信息。

        返回:
            (process_name, window_title) 元组
            process_name: 进程名（如 "chrome.exe"），获取失败返回 ""
            window_title: 窗口标题，获取失败返回 ""
        """
        if not HAS_WIN32 or not HAS_PSUTIL:
            return ("unknown", "unknown")

        try:
            # 获取当前前台窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            # 获取窗口标题
            window_title = win32gui.GetWindowText(hwnd)

            # 根据窗口句柄获取进程 ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            # 根据进程 ID 获取进程对象
            process = psutil.Process(pid)
            process_name = process.name()

            return (process_name, window_title)
        except (win32gui.error, psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            return ("", "")

    def _is_user_idle(self) -> bool:
        """
        检测用户是否空闲（鼠标键盘无操作）。

        返回:
            True = 空闲中，False = 活跃中
        """
        if not HAS_WIN32:
            return False
        try:
            # 获取最后一次输入的时间（鼠标或键盘）
            last_input = win32api.GetLastInputInfo()
            idle_seconds = (win32api.GetTickCount() - last_input) / 1000.0
            return idle_seconds >= IDLE_TIMEOUT
        except Exception:
            return False

    def _classify_process(self, process_name: str) -> str:
        """
        根据进程名判断软件类型。

        返回:
            "work" / "neutral" / "entertainment"
        """
        # 先检查黑白名单
        if self.db.is_whitelisted(process_name):
            return "work"
        if self.db.is_blacklisted(process_name):
            return "entertainment"
        return "neutral"

    def _check_daily_limits(self, process_name: str):
        """
        检查某程序是否超过每日限额，超限则触发回调。
        """
        limits = self.db.get_daily_limits()
        today = date.today().isoformat()

        for limit in limits:
            if limit["process_name"] == process_name and limit["enabled"]:
                used_seconds = self.db.get_daily_usage_for_process(
                    process_name, today
                )
                used_minutes = used_seconds / 60
                limit_minutes = limit["limit_minutes"]

                if (used_minutes >= limit_minutes and
                        self.on_limit_exceeded):
                    self.on_limit_exceeded(
                        process_name, limit_minutes, int(used_minutes)
                    )

    # ================================================================
    # 监控主循环
    # ================================================================

    def _monitor_loop(self):
        """
        监控主循环（在后台线程运行）。
        每 CHECK_INTERVAL 秒检测一次当前窗口。
        """
        while self._running:
            # 检测当前活跃窗口
            process_name, window_title = self._get_active_window_info()

            # 跳过无效检测结果
            if not process_name:
                time.sleep(CHECK_INTERVAL)
                continue

            # 检查用户是否空闲
            if self._is_user_idle():
                # 用户空闲，结束当前记录
                if self._current_record_id is not None:
                    self.db.end_activity(self._current_record_id)
                    self._current_record_id = None
                    self._current_process = None
                time.sleep(CHECK_INTERVAL)
                continue

            # 更新最后活跃时间
            self._last_active_time = datetime.now()

            # 检测窗口是否切换
            if process_name != self._current_process:
                # 结束上一条记录
                if self._current_record_id is not None:
                    self.db.end_activity(self._current_record_id)

                # 开始新记录
                category = self._classify_process(process_name)
                self._current_record_id = self.db.add_activity(
                    process_name, window_title, category
                )
                self._current_process = process_name

                # 触发切换回调
                if self.on_switch:
                    self.on_switch(process_name, window_title)

                # 检查每日限额
                self._check_daily_limits(process_name)
            else:
                # 同一程序，但窗口标题可能变了（如切换网页）
                # TODO: Phase 1 暂不处理网页切换，先记录程序整体使用
                pass

            time.sleep(CHECK_INTERVAL)

    # ================================================================
    # 公开方法
    # ================================================================

    def start(self):
        """启动监控（后台线程）。"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,  # 守护线程，主程序退出时自动结束
            name="ActivityMonitor"
        )
        self._thread.start()
        print("✅ 活动监控已启动")

    def stop(self):
        """停止监控。"""
        self._running = False
        if self._current_record_id is not None:
            self.db.end_activity(self._current_record_id)
            self._current_record_id = None
            self._current_process = None
        print("🛑 活动监控已停止")

    @property
    def is_running(self) -> bool:
        """监控是否正在运行。"""
        return self._running
