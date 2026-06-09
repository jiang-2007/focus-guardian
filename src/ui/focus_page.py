"""
专注模式页面 v2.0
-----------------
番茄钟工作法：专注类型选择、阶段显示、周期计数、休息提醒。
"""

import tkinter as tk
from tkinter import ttk, messagebox

from src.ui.styles import (
    BG_WHITE, BG_LIGHT, PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK,
    PRIMARY_BG, TEXT_PRIMARY, TEXT_SECONDARY, DANGER, WARNING, INFO,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_BIG, CARD_PADDING
)
from src.config import FOCUS_TYPES, DEFAULT_FOCUS_MINUTES


class FocusPage(tk.Frame):
    """专注模式页面 v2.0。"""

    def __init__(self, parent, focus_manager, db_manager):
        super().__init__(parent, bg=BG_LIGHT)
        self.focus = focus_manager
        self.db = db_manager
        self._selected_type = FOCUS_TYPES[0]  # 默认番茄钟
        self._preset_buttons = []

        # 注册回调
        self.focus.on_tick = self._on_tick
        self.focus.on_phase_change = self._on_phase_change
        self.focus.on_finished = self._on_finished
        self.focus.on_blocked = self._on_blocked

        self._build_ui()

    def _build_ui(self):
        """构建页面 UI。"""
        # ---- 顶部标题 ----
        title_bar = tk.Frame(self, bg=BG_WHITE, height=60)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="🍅 专注模式", font=FONT_TITLE,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(side="left", padx=CARD_PADDING, pady=10)

        # ---- 主内容 ----
        content = tk.Frame(self, bg=BG_LIGHT)
        content.pack(fill="both", expand=True, padx=CARD_PADDING, pady=CARD_PADDING)

        # ---- 专注类型选择 ----
        type_frame = tk.Frame(content, bg=BG_WHITE)
        type_frame.pack(fill="x", pady=(0, CARD_PADDING))

        tk.Label(type_frame, text="选择专注类型", font=FONT_BODY,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(anchor="w", padx=CARD_PADDING, pady=(CARD_PADDING, 8))

        self._type_btn_frame = tk.Frame(type_frame, bg=BG_WHITE)
        self._type_btn_frame.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        for ft in FOCUS_TYPES:
            btn = tk.Button(
                self._type_btn_frame,
                text=f"{ft['name']}\n{ft['work_minutes']}min",
                font=("Microsoft YaHei", 8),
                bg=BG_WHITE, fg=TEXT_PRIMARY,
                relief="solid", borderwidth=1,
                padx=8, pady=4,
                command=lambda t=ft: self._select_type(t)
            )
            btn.pack(side="left", padx=(0, 6))
            self._preset_buttons.append((btn, ft["type_id"]))

        self._highlight_type(self._selected_type["type_id"])

        # 自定义时长行
        custom_row = tk.Frame(type_frame, bg=BG_WHITE)
        custom_row.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        tk.Label(custom_row, text="或自定义：专注", font=FONT_SMALL,
                 bg=BG_WHITE, fg=TEXT_SECONDARY).pack(side="left")
        self._custom_work_var = tk.StringVar(value="25")
        self._custom_break_var = tk.StringVar(value="5")
        tk.Spinbox(custom_row, textvariable=self._custom_work_var,
                   from_=1, to=180, width=4, font=FONT_SMALL).pack(side="left", padx=2)
        tk.Label(custom_row, text="分钟  休息", font=FONT_SMALL,
                 bg=BG_WHITE, fg=TEXT_SECONDARY).pack(side="left")
        tk.Spinbox(custom_row, textvariable=self._custom_break_var,
                   from_=0, to=60, width=4, font=FONT_SMALL).pack(side="left", padx=2)
        tk.Label(custom_row, text="分钟", font=FONT_SMALL,
                 bg=BG_WHITE, fg=TEXT_SECONDARY).pack(side="left")

        tk.Button(custom_row, text="使用自定义", font=FONT_SMALL,
                  bg=PRIMARY_BG, fg=PRIMARY, relief="flat", padx=8,
                  command=self._use_custom).pack(side="left", padx=10)

        # ---- 计时器显示区 ----
        timer_frame = tk.Frame(content, bg=BG_WHITE)
        timer_frame.pack(fill="x", pady=(0, CARD_PADDING))

        # 阶段标签
        self.phase_label = tk.Label(timer_frame, text="准备就绪",
                                     font=FONT_HEADING, bg=BG_WHITE, fg=PRIMARY)
        self.phase_label.pack(pady=(15, 0))

        # 大倒计时
        self.timer_label = tk.Label(timer_frame, text=f"{DEFAULT_FOCUS_MINUTES:02d}:00",
                                     font=("Microsoft YaHei", 52, "bold"),
                                     bg=BG_WHITE, fg=PRIMARY)
        self.timer_label.pack(pady=5)

        # 周期计数
        self.cycle_label = tk.Label(timer_frame, text="第 0 轮",
                                     font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_SECONDARY)
        self.cycle_label.pack(pady=(0, 5))

        # 进度条
        self.progress = ttk.Progressbar(timer_frame, mode="determinate", length=420)
        self.progress.pack(pady=(0, 10))

        # ---- 控制按钮 ----
        ctrl_frame = tk.Frame(timer_frame, bg=BG_WHITE)
        ctrl_frame.pack(pady=(0, 15))

        self.start_btn = tk.Button(ctrl_frame, text="▶  开始专注",
                                    font=("Microsoft YaHei", 12, "bold"),
                                    bg=PRIMARY, fg="white", relief="flat",
                                    padx=35, pady=10, cursor="hand2",
                                    command=self._toggle_focus)
        self.start_btn.pack(side="left", padx=5)

        # 严格模式
        self.strict_var = tk.BooleanVar(value=False)
        tk.Checkbutton(ctrl_frame, text="严格模式",
                       variable=self.strict_var, font=FONT_SMALL,
                       bg=BG_WHITE, command=lambda: setattr(
                           self.focus, '_strict_mode', self.strict_var.get())
                       ).pack(side="left", padx=15)

        # ---- 专注历史 ----
        hist_frame = tk.Frame(content, bg=BG_WHITE)
        hist_frame.pack(fill="both", expand=True)

        tk.Label(hist_frame, text="📝 最近专注记录", font=FONT_BODY,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(anchor="w",
                      padx=CARD_PADDING, pady=(CARD_PADDING, 5))

        self.history_text = tk.Text(hist_frame, font=FONT_BODY, bg=BG_WHITE,
                                     fg=TEXT_PRIMARY, height=5, relief="flat",
                                     wrap="word")
        self.history_text.pack(fill="both", expand=True,
                                padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self.history_text.config(state="disabled")

    # ============================================================
    # 事件处理
    # ============================================================

    def _select_type(self, ft: dict):
        """选择预设专注类型。"""
        self._selected_type = ft
        self._highlight_type(ft["type_id"])
        if not self.focus.is_active:
            self.timer_label.config(text=f"{ft['work_minutes']:02d}:00")
            self.progress["value"] = 0

    def _highlight_type(self, type_id: str):
        """高亮选中类型。"""
        for btn, tid in self._preset_buttons:
            if tid == type_id:
                btn.config(bg=PRIMARY, fg="white")
            else:
                btn.config(bg=BG_WHITE, fg=TEXT_PRIMARY)

    def _use_custom(self):
        """使用自定义时长。"""
        try:
            wm = int(self._custom_work_var.get())
            bm = int(self._custom_break_var.get())
        except ValueError:
            messagebox.showwarning("输入错误", "请输入有效的分钟数")
            return
        self._selected_type = {"type_id": "custom", "name": "自定义",
                                "work_minutes": wm, "break_minutes": bm}
        self._highlight_type("custom")
        self.timer_label.config(text=f"{wm:02d}:00")

    def _toggle_focus(self):
        """开始/停止专注。"""
        if self.focus.is_active:
            if messagebox.askyesno("确认", "确定要提前结束专注吗？"):
                self.focus.stop(completed=False)
                self._update_ui_idle()
        else:
            ft = self._selected_type
            wm = ft.get("work_minutes", 25)
            bm = ft.get("break_minutes", 5)
            self.focus.start(work_minutes=wm, break_minutes=bm)
            self._update_ui_active()

    # ============================================================
    # 回调（从后台线程来的，需要用 after）
    # ============================================================

    def _on_tick(self, remaining: int, phase: str):
        self.after(0, lambda: self._update_timer(remaining, phase))

    def _on_phase_change(self, phase: str, message: str):
        self.after(0, lambda: self._update_phase(phase, message))

    def _on_finished(self):
        self.after(0, self._on_focus_completed)

    def _on_blocked(self, process_name: str):
        self.after(0, lambda: self._show_block_warning(process_name))

    # ============================================================
    # UI 更新
    # ============================================================

    def _update_timer(self, remaining: int, phase: str):
        mins = remaining // 60
        secs = remaining % 60
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

        total = self.focus._planned_duration
        progress = ((total - remaining) / total) * 100 if total > 0 else 0
        self.progress["value"] = progress

        self.cycle_label.config(text=f"第 {self.focus.cycle_count + 1} 轮")

        # 休息阶段变橙色
        if phase in ("short_break", "long_break"):
            self.timer_label.config(fg=WARNING)
            self.phase_label.config(text=self.focus.phase_display_name(), fg=WARNING)
        else:
            self.timer_label.config(fg=PRIMARY_DARK)
            self.phase_label.config(text=self.focus.phase_display_name(), fg=PRIMARY)

    def _update_phase(self, phase: str, message: str):
        """阶段切换时的 UI 更新。"""
        self.phase_label.config(text=self.focus.phase_display_name())
        self.cycle_label.config(text=f"第 {self.focus.cycle_count + 1} 轮")
        if phase in ("short_break", "long_break"):
            self.start_btn.config(text="☕ 休息中...", bg=WARNING)
        elif phase == "work":
            self.start_btn.config(text="⏹  停止专注", bg=DANGER)
        # 弹出短暂提示
        if message:
            self.phase_label.config(text=message)

    def _update_ui_active(self):
        self.start_btn.config(text="⏹  停止专注", bg=DANGER)
        self.phase_label.config(text="⚡ 专注中")

    def _update_ui_idle(self):
        self.start_btn.config(text="▶  开始专注", bg=PRIMARY)
        self.phase_label.config(text="准备就绪")
        self.cycle_label.config(text="第 0 轮")
        mins = self._selected_type.get("work_minutes", 25)
        self.timer_label.config(text=f"{mins:02d}:00", fg=PRIMARY)
        self.progress["value"] = 0

    def _on_focus_completed(self):
        self._update_ui_idle()
        self.timer_label.config(text="00:00")
        self.progress["value"] = 100
        total_focus = self.db.get_total_focus_hours()
        messagebox.showinfo("🎉 专注完成",
            f"恭喜！专注时间结束，休息一下吧！\n\n"
            f"累计专注：{total_focus:.1f} 小时")
        self.refresh_history()

    def _show_block_warning(self, process_name: str):
        messagebox.showwarning("专注提醒",
            f"⚠️ 检测到娱乐软件：{process_name}\n\n专注期间请保持专注！")

    # ============================================================
    # 公开方法
    # ============================================================

    def refresh(self):
        if not self.focus.is_active:
            self._update_ui_idle()
        self.refresh_history()

    def refresh_history(self):
        sessions = self.db.get_focus_sessions(limit=10)
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", "end")
        if not sessions:
            self.history_text.insert("1.0", "暂无专注记录，开始你的第一次专注吧！")
        else:
            for s in sessions:
                start = s["start_time"][:16]
                planned = s["planned_duration"] // 60
                actual = s["actual_duration"] // 60
                status = "✅" if s["completed"] else "⚠️"
                line = f"{start} | 计划{planned}min | 实际{actual}min | {status} | 中断{s['interruptions']}次\n"
                self.history_text.insert("end", line)
        self.history_text.config(state="disabled")
