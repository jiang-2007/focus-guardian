"""
新手引导向导
-------------
首次启动时展示的 5 步引导，帮助用户快速上手。
"""

import tkinter as tk
from tkinter import ttk
from src.ui.styles import (
    BG_WHITE, BG_LIGHT, PRIMARY, PRIMARY_DARK, PRIMARY_BG,
    TEXT_PRIMARY, TEXT_SECONDARY, FONT_TITLE, FONT_BODY, FONT_SMALL, CARD_PADDING
)
from src.config import ONBOARDING_STEPS, PRESET_ENTERTAINMENT, PRESET_WORK, PRESET_GAMES


class OnboardingWizard:
    """
    新手引导向导。

    用法:
        wizard = OnboardingWizard(parent, db, on_complete)
        wizard.show()
    """

    def __init__(self, parent, db_manager, on_complete=None):
        """
        参数:
            parent: 父级 Tk 窗口
            db_manager: DatabaseManager 实例
            on_complete: 引导完成后的回调函数
        """
        self.db = db_manager
        self._on_complete = on_complete
        self._step = 0
        self._toplevel = tk.Toplevel(parent)
        self._toplevel.title("🎉 欢迎使用 Focus Guardian")
        self._toplevel.geometry("560x440")
        self._toplevel.resizable(False, False)
        self._toplevel.configure(bg=BG_WHITE)
        self._toplevel.transient(parent)
        self._toplevel.grab_set()

        self._build_ui()
        self._show_step(0)

    def _build_ui(self):
        """构建引导窗口 UI。"""
        # 顶部进度条
        self._progress_frame = tk.Frame(self._toplevel, bg=BG_LIGHT, height=6)
        self._progress_frame.pack(fill="x")
        self._progress_bar = tk.Frame(self._progress_frame, bg=PRIMARY, height=6, width=0)
        self._progress_bar.pack(side="left")
        # 不 propagate

        # 主内容区
        self._content = tk.Frame(self._toplevel, bg=BG_WHITE)
        self._content.pack(fill="both", expand=True, padx=30, pady=25)

        # 步骤图标
        self._icon_label = tk.Label(self._content, text="", font=("Microsoft YaHei", 48),
                                     bg=BG_WHITE)
        self._icon_label.pack(pady=(10, 5))

        # 标题
        self._title_label = tk.Label(self._content, text="", font=FONT_TITLE,
                                      bg=BG_WHITE, fg=TEXT_PRIMARY)
        self._title_label.pack(pady=(0, 10))

        # 描述
        self._desc_label = tk.Label(self._content, text="", font=FONT_BODY,
                                     bg=BG_WHITE, fg=TEXT_SECONDARY, wraplength=480,
                                     justify="center")
        self._desc_label.pack(pady=(0, 15))

        # 操作区
        self._action_frame = tk.Frame(self._content, bg=BG_WHITE)
        self._action_frame.pack(pady=10)

        # 底部按钮
        bottom = tk.Frame(self._toplevel, bg=BG_WHITE)
        bottom.pack(fill="x", padx=30, pady=(0, 20))

        self._skip_btn = tk.Button(bottom, text="跳过引导", font=FONT_SMALL,
                                    bg=BG_WHITE, fg=TEXT_SECONDARY, relief="flat",
                                    cursor="hand2", command=self._finish)
        self._skip_btn.pack(side="left")

        self._nav_frame = tk.Frame(bottom, bg=BG_WHITE)
        self._nav_frame.pack(side="right")

        self._prev_btn = tk.Button(self._nav_frame, text="◀ 上一步", font=FONT_BODY,
                                    bg=BG_WHITE, fg=TEXT_PRIMARY, relief="flat",
                                    padx=15, pady=6, cursor="hand2",
                                    command=self._prev)
        self._prev_btn.pack(side="left", padx=5)

        self._next_btn = tk.Button(self._nav_frame, text="下一步 ▶", font=FONT_BODY,
                                    bg=PRIMARY, fg="white", relief="flat",
                                    padx=15, pady=6, cursor="hand2",
                                    command=self._next)
        self._next_btn.pack(side="left", padx=5)

    # ============================================================
    # 步骤管理
    # ============================================================

    def _show_step(self, step_index: int):
        """显示指定步骤。"""
        total = len(ONBOARDING_STEPS)
        step_data = ONBOARDING_STEPS[step_index]

        # 更新进度条
        self._progress_bar.config(width=(560 * (step_index + 1)) // total)

        # 图标映射
        icons = ["🛡️", "🚫", "🍅", "📊", "⏰"]
        self._icon_label.config(text=icons[step_index])

        # 标题和描述
        self._title_label.config(text=f"Step {step_index + 1}/{total}: {step_data['title']}")
        self._desc_label.config(text=step_data["description"])

        # 清空操作区
        for w in self._action_frame.winfo_children():
            w.destroy()

        # 步骤 1：导入模板
        if step_index == 1:
            tk.Button(self._action_frame,
                      text="📥 一键导入娱乐软件模板（推荐）",
                      font=FONT_BODY, bg=PRIMARY, fg="white",
                      relief="flat", padx=20, pady=8, cursor="hand2",
                      command=self._import_templates).pack()
            tk.Label(self._action_frame, text="稍后可在设置页面手动管理",
                     font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_SECONDARY).pack(pady=5)

        # 步骤 2：跳转专注页
        elif step_index == 2:
            tk.Button(self._action_frame,
                      text="🍅 前往专注页面",
                      font=FONT_BODY, bg=PRIMARY, fg="white",
                      relief="flat", padx=20, pady=8, cursor="hand2",
                      command=self._finish).pack()

        # 按钮状态
        self._prev_btn.pack_forget() if step_index == 0 else self._prev_btn.pack(
            side="left", padx=5)

        if step_index == total - 1:
            self._next_btn.config(text="✅ 完成", bg=PRIMARY_DARK)
        else:
            self._next_btn.config(text="下一步 ▶", bg=PRIMARY)

    def _next(self):
        """下一步。"""
        if self._step < len(ONBOARDING_STEPS) - 1:
            self._step += 1
            self._show_step(self._step)
        else:
            self._finish()

    def _prev(self):
        """上一步。"""
        if self._step > 0:
            self._step -= 1
            self._show_step(self._step)

    def _import_templates(self):
        """导入预设模板。"""
        count = 0
        for item in PRESET_ENTERTAINMENT + PRESET_GAMES:
            self.db.add_to_blacklist(item["process_name"],
                                      item.get("display_name", item["process_name"]))
            count += 1
        for item in PRESET_WORK:
            self.db.add_to_whitelist(item["process_name"],
                                      item.get("display_name", item["process_name"]))
            count += 1
        tk.Label(self._action_frame, text=f"✅ 已导入 {count} 个预设软件！",
                 font=FONT_BODY, bg=BG_WHITE, fg=PRIMARY_DARK).pack(pady=10)

    def _finish(self):
        """完成引导。"""
        self.db.mark_onboarding_done()
        self._toplevel.destroy()
        if self._on_complete:
            self._on_complete()

    def show(self):
        """显示引导窗口并等待用户完成。"""
        self._toplevel.wait_window()
