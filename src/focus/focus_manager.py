"""
专注模式管理器 v2.0
-------------------
番茄钟工作法：专注 + 休息轮换，支持多轮循环。
检测并拦截黑名单软件，记录专注历史。
"""

import time
import threading
from datetime import datetime

from src.config import (
    STRICT_MODE_DEFAULT,
    DEFAULT_FOCUS_MINUTES,
    POMODORO_WORK_MINUTES,
    POMODORO_SHORT_BREAK,
    POMODORO_LONG_BREAK,
    POMODORO_CYCLES_BEFORE_LONG_BREAK,
    REST_REMIND_INTERVAL,
)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class FocusManager:
    """
    专注模式管理器 v2.0。

    新增番茄钟功能：
    - 专注阶段（work）→ 短休息（short_break）→ 专注 → ... → 长休息（long_break）
    - 每 4 轮进入一次长休息
    - 支持自定义专注/休息时长
    """

    def __init__(self, db_manager):
        """初始化专注管理器。"""
        self.db = db_manager

        # 状态
        self._active = False
        self._phase = "idle"          # idle / work / short_break / long_break
        self._start_time = None
        self._planned_duration = 0    # 当前阶段计划秒数
        self._remaining = 0           # 当前阶段剩余秒数
        self._session_id = None       # 专注记录 ID
        self._interruptions = 0
        self._strict_mode = STRICT_MODE_DEFAULT

        # 番茄钟统计
        self._cycle_count = 0         # 当前已完成循环数
        self._total_work_seconds = 0  # 累计专注秒数
        self._rest_remaining = 0

        # 线程
        self._timer_thread = None
        self._blocker_thread = None
        self._rest_reminder_thread = None
        self._last_user_active = datetime.now()

        # 回调函数
        self.on_tick = None           # func(remaining_seconds, phase)
        self.on_phase_change = None   # func(phase, message)
        self.on_finished = None       # func()
        self.on_blocked = None        # func(process_name)
        self.on_rest_reminder = None  # func()

    # ============================================================
    # 专注控制
    # ============================================================

    def start(self, duration_minutes=None, work_minutes=None, break_minutes=None):
        """
        开始专注模式。优先使用 work_minutes/break_minutes（番茄钟模式）。

        参数:
            duration_minutes: 传统模式专注时长（分钟），无休息
            work_minutes: 番茄钟模式专注时长（分钟）
            break_minutes: 番茄钟模式休息时长（分钟）
        """
        if self._active:
            return

        if work_minutes is not None:
            self._work_minutes = work_minutes
            self._break_short_minutes = break_minutes if break_minutes else POMODORO_SHORT_BREAK
            self._break_long_minutes = max(self._break_short_minutes * 3, POMODORO_LONG_BREAK)
            self._pomodoro_mode = True
            start_minutes = work_minutes
        elif duration_minutes is not None:
            self._work_minutes = duration_minutes
            self._break_short_minutes = 0
            self._break_long_minutes = 0
            self._pomodoro_mode = False
            start_minutes = duration_minutes
        else:
            self._work_minutes = DEFAULT_FOCUS_MINUTES
            self._break_short_minutes = 0
            self._break_long_minutes = 0
            self._pomodoro_mode = False
            start_minutes = DEFAULT_FOCUS_MINUTES

        self._active = True
        self._phase = "work"
        self._start_time = datetime.now()
        self._planned_duration = start_minutes * 60
        self._remaining = self._planned_duration
        self._interruptions = 0
        self._cycle_count = 0
        self._total_work_seconds = 0

        # 保存到数据库
        self._session_id = self.db.add_focus_session(self._planned_duration)

        # 启动后台线程
        self._timer_thread = threading.Thread(target=self._countdown_loop, daemon=True)
        self._timer_thread.start()

        self._blocker_thread = threading.Thread(target=self._blocker_loop, daemon=True)
        self._blocker_thread.start()

        print(f"🍅 专注模式已开启"
              + (f"（番茄钟: {self._work_minutes}min 专注 / {self._break_short_minutes}min 休息）"
                 if self._pomodoro_mode else f"，时长 {start_minutes} 分钟"))

    def stop(self, completed=False):
        """停止专注模式。"""
        if not self._active:
            return
        self._active = False
        if self._session_id is not None:
            self.db.end_focus_session(
                self._session_id,
                interruptions=self._interruptions,
                completed=completed
            )
        self._phase = "idle"
        print("✅ 专注模式已结束" if completed else "⚠️ 专注模式已中断")

    def toggle_strict_mode(self) -> bool:
        """切换严格模式。"""
        self._strict_mode = not self._strict_mode
        return self._strict_mode

    # ============================================================
    # 番茄钟阶段切换
    # ============================================================

    def _advance_phase(self):
        """切换到下一个番茄钟阶段。"""
        if self._phase == "work":
            self._total_work_seconds += self._planned_duration - self._remaining
            self._cycle_count += 1

            if self._pomodoro_mode and self._break_short_minutes > 0:
                # 每 N 个循环进入长休息
                if self._cycle_count % POMODORO_CYCLES_BEFORE_LONG_BREAK == 0:
                    self._phase = "long_break"
                    self._planned_duration = self._break_long_minutes * 60
                else:
                    self._phase = "short_break"
                    self._planned_duration = self._break_short_minutes * 60
                self._remaining = self._planned_duration
                if self.on_phase_change:
                    break_type = "长休息" if self._phase == "long_break" else "短休息"
                    self.on_phase_change(self._phase,
                        f"☕ 第 {self._cycle_count} 轮完成！进入{break_type} {self._planned_duration // 60} 分钟")
            else:
                self.stop(completed=True)
                if self.on_finished:
                    self.on_finished()
                return

        elif self._phase in ("short_break", "long_break"):
            # 休息结束，进入下一轮专注
            self._phase = "work"
            self._planned_duration = self._work_minutes * 60
            self._remaining = self._planned_duration
            if self.on_phase_change:
                self.on_phase_change("work",
                    f"🚀 休息结束！开始第 {self._cycle_count + 1} 轮专注 {self._work_minutes} 分钟")

    # ============================================================
    # 内部循环
    # ============================================================

    def _countdown_loop(self):
        """倒计时循环（每秒更新）。"""
        while self._active and self._remaining > 0:
            time.sleep(1)
            self._remaining -= 1
            if self.on_tick:
                self.on_tick(self._remaining, self._phase)

        # 当前阶段结束，切换
        if self._active:
            self._advance_phase()
            # 如果还在活跃（进入了新阶段），重启倒计时
            if self._active:
                threading.Thread(target=self._countdown_loop, daemon=True).start()

    def _blocker_loop(self):
        """拦截检测循环。"""
        # 只在专注阶段检测
        while self._active:
            if self._phase == "work":
                self._check_and_block()
            time.sleep(2)

    def _check_and_block(self):
        """检测并拦截黑名单进程。"""
        if not HAS_PSUTIL:
            return
        blacklist = self.db.get_blacklist()
        blacklist_names = {item["process_name"].lower() for item in blacklist}
        if not blacklist_names:
            return
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info["name"]
                if name and name.lower() in blacklist_names:
                    if self._strict_mode:
                        proc.terminate()
                        self._interruptions += 1
                    else:
                        if self.on_blocked:
                            self.on_blocked(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    # ============================================================
    # 状态查询
    # ============================================================

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def remaining_seconds(self) -> int:
        return self._remaining

    @property
    def planned_minutes(self) -> int:
        return self._planned_duration // 60

    @property
    def cycle_count(self) -> int:
        return self._cycle_count

    @property
    def elapsed_seconds(self) -> int:
        return self._planned_duration - self._remaining

    @property
    def progress_percent(self) -> float:
        if self._planned_duration == 0:
            return 0
        return (self.elapsed_seconds / self._planned_duration) * 100

    def format_remaining(self) -> str:
        mins = self._remaining // 60
        secs = self._remaining % 60
        return f"{mins:02d}:{secs:02d}"

    def phase_display_name(self) -> str:
        """返回当前阶段的显示名称。"""
        names = {
            "work": "⚡ 专注中",
            "short_break": "☕ 短休息",
            "long_break": "🧘 长休息",
            "idle": "准备就绪",
        }
        return names.get(self._phase, self._phase)
