"""
报表页面 v2.0
-------------
日/周/月视图切换 + 活动记录表格 + 数据导出 + 删除功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, timedelta
import calendar

from src.ui.styles import (
    BG_WHITE, BG_LIGHT, PRIMARY, PRIMARY_DARK, PRIMARY_BG, PRIMARY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, DANGER, INFO,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, CARD_PADDING
)


class ReportPage(tk.Frame):
    """报表页面 v2.0。"""

    def __init__(self, parent, db_manager):
        super().__init__(parent, bg=BG_LIGHT)
        self.db = db_manager
        self._current_date = date.today().isoformat()
        self._view_mode = "day"  # day / week / month
        self._build_ui()

    def _build_ui(self):
        # 标题
        title_bar = tk.Frame(self, bg=BG_WHITE, height=60)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="📋 使用报表", font=FONT_TITLE,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(side="left", padx=CARD_PADDING, pady=10)

        # 视图切换 + 日期导航
        nav_frame = tk.Frame(self, bg=BG_WHITE)
        nav_frame.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        # 视图按钮
        view_row = tk.Frame(nav_frame, bg=BG_WHITE)
        view_row.pack(side="left", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        self._day_btn = tk.Button(view_row, text="📅 日视图", font=FONT_SMALL,
                                   bg=PRIMARY, fg="white", relief="flat",
                                   padx=10, pady=3, cursor="hand2",
                                   command=lambda: self._switch_view("day"))
        self._day_btn.pack(side="left", padx=2)

        self._week_btn = tk.Button(view_row, text="📊 周视图", font=FONT_SMALL,
                                    bg=BG_WHITE, fg=TEXT_PRIMARY, relief="flat",
                                    padx=10, pady=3, cursor="hand2",
                                    command=lambda: self._switch_view("week"))
        self._week_btn.pack(side="left", padx=2)

        self._month_btn = tk.Button(view_row, text="📈 月视图", font=FONT_SMALL,
                                     bg=BG_WHITE, fg=TEXT_PRIMARY, relief="flat",
                                     padx=10, pady=3, cursor="hand2",
                                     command=lambda: self._switch_view("month"))
        self._month_btn.pack(side="left", padx=2)

        # 日期选择器
        nav_inner = tk.Frame(nav_frame, bg=BG_WHITE)
        nav_inner.pack(fill="x", padx=CARD_PADDING, pady=(5, CARD_PADDING))

        tk.Button(nav_inner, text="◀", font=FONT_BODY, bg=BG_WHITE,
                  fg=TEXT_PRIMARY, relief="flat", padx=5, cursor="hand2",
                  command=self._prev_period).pack(side="left")
        self.date_label = tk.Label(nav_inner, text="",
                                    font=FONT_BODY, bg=BG_WHITE,
                                    fg=PRIMARY_DARK, width=24)
        self.date_label.pack(side="left")
        tk.Button(nav_inner, text="▶", font=FONT_BODY, bg=BG_WHITE,
                  fg=TEXT_PRIMARY, relief="flat", padx=5, cursor="hand2",
                  command=self._next_period).pack(side="left")
        tk.Button(nav_inner, text="今天", font=FONT_SMALL, bg=PRIMARY_BG,
                  fg=PRIMARY, relief="flat", padx=10, pady=2, cursor="hand2",
                  command=self._go_today).pack(side="left", padx=8)

        # 导出按钮
        exp_row = tk.Frame(nav_inner, bg=BG_WHITE)
        exp_row.pack(side="right")
        for fmt, lbl in [("txt", "导出 TXT"), ("csv", "导出 CSV")]:
            tk.Button(exp_row, text=lbl, font=FONT_SMALL,
                      bg=PRIMARY if fmt == "txt" else PRIMARY_BG,
                      fg="white" if fmt == "txt" else PRIMARY,
                      relief="flat", padx=10, pady=2, cursor="hand2",
                      command=lambda f=fmt: self._export(f)).pack(side="left", padx=2)
        tk.Button(exp_row, text="删除当前", font=FONT_SMALL, bg=DANGER,
                  fg="white", relief="flat", padx=10, pady=2, cursor="hand2",
                  command=self._delete_current).pack(side="left", padx=2)

        # 汇总行
        self.summary_label = tk.Label(self, text="总使用时长：计算中...",
                                       font=FONT_BODY, bg=BG_LIGHT, fg=TEXT_PRIMARY)
        self.summary_label.pack(anchor="w", padx=CARD_PADDING * 2, pady=(5, 0))

        # 表格
        table_frame = tk.Frame(self, bg=BG_WHITE)
        table_frame.pack(fill="both", expand=True,
                         padx=CARD_PADDING, pady=(CARD_PADDING, CARD_PADDING))

        columns = ("time_range", "process", "title", "duration")
        self.tree = ttk.Treeview(table_frame, columns=columns,
                                  show="headings", height=12)
        self.tree.heading("time_range", text="时间段")
        self.tree.heading("process", text="程序")
        self.tree.heading("title", text="窗口标题")
        self.tree.heading("duration", text="时长")
        self.tree.column("time_range", width=180)
        self.tree.column("process", width=140)
        self.tree.column("title", width=240)
        self.tree.column("duration", width=90)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # 删除选中
        del_frame = tk.Frame(self, bg=BG_LIGHT)
        del_frame.pack(fill="x", padx=CARD_PADDING)
        tk.Button(del_frame, text="删除选中记录", font=FONT_SMALL,
                  bg=DANGER, fg="white", relief="flat", padx=10, pady=3,
                  cursor="hand2", command=self._delete_selected).pack(side="right")

        self._update_date_label()
        self.refresh()

    # ============================================================
    # 视图切换
    # ============================================================

    def _switch_view(self, mode: str):
        self._view_mode = mode
        for btn, m in [(self._day_btn, "day"), (self._week_btn, "week"),
                        (self._month_btn, "month")]:
            if m == mode:
                btn.config(bg=PRIMARY, fg="white")
            else:
                btn.config(bg=BG_WHITE, fg=TEXT_PRIMARY)
        if mode != "day":
            self._current_date = date.today().isoformat()
        self._update_date_label()
        self.refresh()

    def _update_date_label(self):
        dt = date.fromisoformat(self._current_date)
        wd = ["周一","周二","周三","周四","周五","周六","周日"][dt.weekday()]
        if self._view_mode == "day":
            self.date_label.config(text=f"{dt.strftime('%Y年%m月%d日')} {wd}")
        elif self._view_mode == "week":
            monday = dt - timedelta(days=dt.weekday())
            sunday = monday + timedelta(days=6)
            self.date_label.config(
                text=f"{monday.strftime('%m/%d')} ~ {sunday.strftime('%m/%d')}  第{dt.isocalendar()[1]}周")
        else:
            self.date_label.config(text=f"{dt.strftime('%Y年%m月')}")

    def _prev_period(self):
        dt = date.fromisoformat(self._current_date)
        if self._view_mode == "day":
            self._current_date = (dt - timedelta(days=1)).isoformat()
        elif self._view_mode == "week":
            self._current_date = (dt - timedelta(days=7)).isoformat()
        else:
            y, m = dt.year, dt.month
            if m == 1:
                self._current_date = date(y - 1, 12, 1).isoformat()
            else:
                self._current_date = date(y, m - 1, 1).isoformat()
        self._update_date_label()
        self.refresh()

    def _next_period(self):
        dt = date.fromisoformat(self._current_date)
        today = date.today()
        if self._view_mode == "day":
            if dt >= today: return
            self._current_date = (dt + timedelta(days=1)).isoformat()
        elif self._view_mode == "week":
            next_w = dt + timedelta(days=7)
            if next_w > today: return
            self._current_date = next_w.isoformat()
        else:
            y, m = dt.year, dt.month
            if m == 12:
                nm = date(y + 1, 1, 1)
            else:
                nm = date(y, m + 1, 1)
            if nm > today: return
            self._current_date = nm.isoformat()
        self._update_date_label()
        self.refresh()

    def _go_today(self):
        self._current_date = date.today().isoformat()
        self._view_mode = "day"
        self._switch_view("day")
        self._update_date_label()
        self.refresh()

    # ============================================================
    # 格式化
    # ============================================================

    def _fmt_dur(self, sec: int) -> str:
        if sec < 60: return f"{sec}秒"
        if sec < 3600: return f"{sec // 60}分钟"
        h, m = divmod(sec, 3600); return f"{h}h{m // 60}m"

    # ============================================================
    # 操作
    # ============================================================

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要删除的记录")
            return
        if messagebox.askyesno("确认", f"确定要删除 {len(sel)} 条记录吗？"):
            for s in sel:
                rid = self.tree.item(s, "tags")[0]
                self.db.delete_activity(int(rid))
            self.refresh()

    def _delete_current(self):
        label = self.date_label.cget("text")
        if self._view_mode != "day":
            messagebox.showinfo("提示", "周/月视图暂不支持一键删除，请切换到日视图")
            return
        if messagebox.askyesno("⚠️ 确认", f"确定要删除 {label} 的所有记录吗？"):
            self.db.delete_activities_by_date(self._current_date)
            self.refresh()
            messagebox.showinfo("完成", "已删除")

    def _export(self, fmt: str):
        activities = self.db.get_activities_by_date(self._current_date)
        if not activities:
            messagebox.showinfo("提示", "没有可导出的记录")
            return
        fname = f"FocusGuardian_{self._current_date}.{fmt}"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} 文件", f"*.{fmt}")],
            initialfile=fname)
        if not path: return
        from src.utils.export import export_activities
        export_activities(activities, path, fmt)
        messagebox.showinfo("导出完成", f"✅ 已导出到：\n{path}")

    # ============================================================
    # 公开刷新
    # ============================================================

    def refresh(self):
        dt = date.fromisoformat(self._current_date)

        if self._view_mode == "day":
            activities = self.db.get_activities_by_date(self._current_date)
            total = sum(a["duration"] for a in activities)
            self.summary_label.config(
                text=f"当日总时长：{self._fmt_dur(total)}  |  {len(activities)} 条记录")
        elif self._view_mode == "week":
            monday = dt - timedelta(days=dt.weekday())
            weekly = self.db.get_weekly_stats(monday.isoformat())
            total = sum(d["total_seconds"] for d in weekly)
            # 取本周所有日期的活动
            activities = []
            for d in weekly:
                day_acts = self.db.get_activities_by_date(d["date"])
                activities.extend(day_acts)
            self.summary_label.config(
                text=f"本周总时长：{self._fmt_dur(total)}  |  {len(activities)} 条记录")
        else:
            monthly = self.db.get_monthly_stats(dt.year, dt.month)
            total = sum(d["total_seconds"] for d in monthly)
            activities = []
            for d in monthly:
                if d["total_seconds"] > 0:
                    day_acts = self.db.get_activities_by_date(d["date"])
                    activities.extend(day_acts)
            self.summary_label.config(
                text=f"本月总时长：{self._fmt_dur(total)}  |  {len(activities)} 条记录")

        # 填充表格
        for row in self.tree.get_children():
            self.tree.delete(row)

        for a in sorted(activities, key=lambda x: x["start_time"], reverse=True)[:200]:
            st = a["start_time"][11:16] if a["start_time"] else ""
            et = a.get("end_time", "") or ""
            et = et[11:16] if et else "..."
            self.tree.insert("", "end", values=(
                f"{st} ~ {et}",
                a["process_name"],
                (a.get("window_title", "") or "")[:50],
                self._fmt_dur(a.get("duration", 0)),
            ), tags=(str(a["id"]),))
