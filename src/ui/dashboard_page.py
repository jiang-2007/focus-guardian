"""
仪表盘页面 v2.0
---------------
今日概览 + 周统计柱状图 + 分类饼图 + Top 5 程序。
所有图表用 tkinter Canvas 自绘，无第三方依赖。
"""

import tkinter as tk
from tkinter import ttk
from datetime import date, timedelta
import math

from src.ui.styles import (
    BG_WHITE, BG_LIGHT, PRIMARY, PRIMARY_LIGHT, PRIMARY_DARK, PRIMARY_BG,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    COLOR_WORK, COLOR_NEUTRAL, COLOR_ENTERTAINMENT, DANGER, WARNING, INFO,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, FONT_BIG, CARD_PADDING
)


class DashboardPage(tk.Frame):
    """仪表盘页面 v2.0。"""

    def __init__(self, parent, db_manager):
        super().__init__(parent, bg=BG_LIGHT)
        self.db = db_manager
        self._chart_week_data = []
        self._chart_pie_data = []
        self._build_ui()

    def _build_ui(self):
        """构建页面 UI。"""
        # ---- 顶部标题栏 ----
        title_bar = tk.Frame(self, bg=BG_WHITE, height=60)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(title_bar, text="📊 数据看板",
                 font=FONT_TITLE, bg=BG_WHITE, fg=TEXT_PRIMARY
                 ).pack(side="left", padx=CARD_PADDING, pady=10)

        today_str = date.today().strftime("%Y年%m月%d日")
        tk.Label(title_bar, text=today_str,
                 font=FONT_BODY, bg=BG_WHITE, fg=TEXT_SECONDARY
                 ).pack(side="right", padx=CARD_PADDING, pady=10)

        # ---- 可滚动内容区 ----
        canvas = tk.Canvas(self, bg=BG_LIGHT, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=BG_LIGHT)

        # 创建 Canvas 窗口（使用 tag 以便后续调整大小）
        canvas.create_window((0, 0), window=self._scroll_frame,
                            anchor="nw", tags="inner_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Canvas 大小变化时同步窗口宽度
        def _on_canvas_resize(event):
            canvas.itemconfigure("inner_frame", width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        # 内容变化时更新滚动区域
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._scroll_frame.bind("<Configure>", _on_frame_configure)

        self._canvas_ref = canvas
        self._scrollbar_ref = scrollbar

        # 鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # 卡片行1
        row1 = tk.Frame(self._scroll_frame, bg=BG_LIGHT)
        row1.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        self.total_card = self._make_card(row1, "⏱️ 今日总时长", "0小时 0分钟")
        self.total_card.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.apps_card = self._make_card(row1, "🖥️ 使用程序", "0 个")
        self.apps_card.pack(side="left", fill="both", expand=True, padx=4)
        self.focus_card = self._make_card(row1, "🍅 今日专注", "0 次")
        self.focus_card.pack(side="left", fill="both", expand=True, padx=4)
        self.streak_card = self._make_card(row1, "🔥 连续天数", "0 天")
        self.streak_card.pack(side="left", fill="both", expand=True, padx=(4, 0))

        # 图表行：周柱状图 + 分类饼图
        row2 = tk.Frame(self._scroll_frame, bg=BG_LIGHT)
        row2.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        # 左：周统计
        self._week_frame = tk.Frame(row2, bg=BG_WHITE)
        self._week_frame.pack(side="left", fill="both", expand=True, padx=(0, 4))

        tk.Label(self._week_frame, text="📅 本周使用趋势",
                 font=FONT_HEADING, bg=BG_WHITE, fg=TEXT_PRIMARY
                 ).pack(anchor="w", padx=CARD_PADDING, pady=(CARD_PADDING, 2))

        self._week_canvas = tk.Canvas(self._week_frame, bg=BG_WHITE,
                                       height=200, highlightthickness=0)
        self._week_canvas.pack(fill="both", expand=True,
                                padx=CARD_PADDING, pady=(0, CARD_PADDING))

        # 右：分类占比
        self._pie_frame = tk.Frame(row2, bg=BG_WHITE)
        self._pie_frame.pack(side="right", fill="both", expand=True, padx=(4, 0))

        tk.Label(self._pie_frame, text="🥧 今日分类占比",
                 font=FONT_HEADING, bg=BG_WHITE, fg=TEXT_PRIMARY
                 ).pack(anchor="w", padx=CARD_PADDING, pady=(CARD_PADDING, 2))

        self._pie_canvas = tk.Canvas(self._pie_frame, bg=BG_WHITE,
                                      height=200, highlightthickness=0)
        self._pie_canvas.pack(fill="both", expand=True,
                               padx=CARD_PADDING, pady=(0, CARD_PADDING))
        self._pie_legend = tk.Frame(self._pie_frame, bg=BG_WHITE)
        self._pie_legend.pack(fill="x", padx=CARD_PADDING, pady=(0, 5))

        # Top 5 程序
        self._top5_section = tk.Frame(self._scroll_frame, bg=BG_WHITE)
        self._top5_section.pack(fill="x", padx=CARD_PADDING, pady=CARD_PADDING)

        tk.Label(self._top5_section, text="📋 今日最常使用 Top 5",
                 font=FONT_HEADING, bg=BG_WHITE, fg=TEXT_PRIMARY
                 ).pack(anchor="w", padx=CARD_PADDING, pady=(CARD_PADDING, 5))

        self._top5_list = tk.Frame(self._top5_section, bg=BG_WHITE)
        self._top5_list.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

    # ============================================================
    # 辅助方法
    # ============================================================

    def _make_card(self, parent, title, value) -> tk.Frame:
        """创建统计卡片。"""
        card = tk.Frame(parent, bg=BG_WHITE, highlightbackground="#E0E0E0",
                        highlightthickness=1)
        tk.Label(card, text=title,
                 font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_SECONDARY
                 ).pack(anchor="w", padx=10, pady=(10, 2))
        vl = tk.Label(card, text=value,
                      font=FONT_BIG, bg=BG_WHITE, fg=PRIMARY)
        vl.pack(anchor="w", padx=10, pady=(0, 10))
        card.value_label = vl
        return card

    def _format_duration(self, total_seconds: int) -> str:
        if total_seconds <= 0:
            return "0分钟"
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}小时 {minutes}分钟"
        return f"{minutes}分钟"

    def _format_minutes(self, total_seconds: int) -> str:
        """格式化为分钟数用于图表标注。"""
        m = max(1, total_seconds // 60)
        if m >= 60:
            return f"{m // 60}h{m % 60}m"
        return f"{m}m"

    # ============================================================
    # 柱状图绘制（本周趋势）
    # ============================================================

    def _draw_week_chart(self, weekly_data: list):
        """在 Canvas 上绘制本周柱状图。"""
        c = self._week_canvas
        c.delete("all")

        if not weekly_data:
            c.create_text(100, 100, text="暂无数据",
                          font=FONT_SMALL, fill=TEXT_HINT)
            return

        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50: w = 400   # Canvas 未布局时宽度为 1，用合理默认值
        if h < 50: h = 200
        pad_l, pad_r, pad_t, pad_b = 30, 15, 15, 30

        values = [d["total_seconds"] for d in weekly_data]
        max_val = max(values) if max(values) > 0 else 1

        labels = []
        for d in weekly_data:
            dt = date.fromisoformat(d["date"])
            labels.append(["一","二","三","四","五","六","日"][dt.weekday()])

        bar_count = len(weekly_data)
        bar_area_w = w - pad_l - pad_r
        bar_w = max(6, min(40, (bar_area_w / bar_count) * 0.65))
        gap = bar_area_w / bar_count

        # 网格线
        for pct in [0.25, 0.5, 0.75, 1.0]:
            y = pad_t + (1 - pct) * (h - pad_t - pad_b)
            c.create_line(pad_l, y, w - pad_r, y, fill="#E0E0E0", dash=(2, 4))

        for i, (item, label) in enumerate(zip(weekly_data, labels)):
            val = item["total_seconds"]
            bar_h = max(2, (val / max_val) * (h - pad_t - pad_b))
            x1 = pad_l + i * gap + (gap - bar_w) / 2
            y1 = h - pad_b - bar_h
            x2 = x1 + bar_w
            y2 = h - pad_b

            # 根据日期，今天的柱子用主色高亮
            color = PRIMARY if item["date"] == date.today().isoformat() else PRIMARY_LIGHT
            c.create_rectangle(x1, y1, x2, y2, fill=color, outline="",
                               tags="bar")
            # 数值标注
            if val > 0:
                c.create_text((x1 + x2) / 2, y1 - 8,
                              text=self._format_minutes(val),
                              font=("Microsoft YaHei", 7), fill=TEXT_SECONDARY)
            # X 轴标签
            c.create_text((x1 + x2) / 2, y2 + 12,
                          text=label,
                          font=("Microsoft YaHei", 8), fill=TEXT_SECONDARY)

    # ============================================================
    # 饼图绘制（分类占比）
    # ============================================================

    def _draw_pie_chart(self, cat_data: list):
        """在 Canvas 上绘制分类饼图。"""
        c = self._pie_canvas
        c.delete("all")
        for w in self._pie_legend.winfo_children():
            w.destroy()

        if not cat_data or sum(d["total_seconds"] for d in cat_data) == 0:
            c.create_text(100, 100, text="今日暂无使用",
                          font=FONT_SMALL, fill=TEXT_HINT)
            return

        colors_map = {"work": COLOR_WORK, "neutral": COLOR_NEUTRAL,
                      "entertainment": COLOR_ENTERTAINMENT}
        labels_map = {"work": "🟢 工作", "neutral": "🟡 中性", "entertainment": "🔴 娱乐"}

        total = sum(d["total_seconds"] for d in cat_data)
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 50: w = 300
        if h < 50: h = 200
        cx, cy = 80, h // 2
        radius = min(70, h // 2 - 10)

        start_angle = -90
        for item in cat_data:
            if item["total_seconds"] <= 0:
                continue
            extent = (item["total_seconds"] / total) * 360
            color = colors_map.get(item["category"], TEXT_HINT)
            c.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                         start=start_angle, extent=extent,
                         fill=color, outline=BG_WHITE, width=2)
            start_angle += extent

        # 中心空白（甜甜圈效果）
        inner_r = radius * 0.45
        c.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                      fill=BG_WHITE, outline="")
        c.create_text(cx, cy, text=self._format_duration(total),
                      font=("Microsoft YaHei", 9, "bold"), fill=TEXT_PRIMARY)

        # 图例
        for item in cat_data:
            if item["total_seconds"] <= 0:
                continue
            color = colors_map.get(item["category"], TEXT_HINT)
            lbl = labels_map.get(item["category"], item["category"])
            pct = (item["total_seconds"] / total) * 100
            fr = tk.Frame(self._pie_legend, bg=BG_WHITE)
            fr.pack(side="left", padx=6)
            tk.Label(fr, text="●", font=("Microsoft YaHei", 10),
                     fg=color, bg=BG_WHITE).pack(side="left")
            tk.Label(fr, text=f"{lbl} {pct:.0f}%",
                     font=("Microsoft YaHei", 8), bg=BG_WHITE, fg=TEXT_SECONDARY
                     ).pack(side="left")

    # ============================================================
    # Top 5 列表
    # ============================================================

    def _draw_top5(self, top5: list):
        """绘制 Top 5 程序列表。"""
        for widget in self._top5_list.winfo_children():
            widget.destroy()

        if not top5:
            tk.Label(self._top5_list, text="暂无数据，请保持程序运行一段时间后查看",
                     font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_HINT).pack(pady=15)
            return

        # 表头
        hdr = tk.Frame(self._top5_list, bg=BG_WHITE)
        hdr.pack(fill="x", pady=(0, 4))
        for text, w in [("#", 3), ("程序", 20), ("时长", 12), ("次数", 6)]:
            tk.Label(hdr, text=text, font=("Microsoft YaHei", 9, "bold"),
                     bg=BG_WHITE, fg=TEXT_HINT, width=w, anchor="w"
                     ).pack(side="left")

        for i, item in enumerate(top5):
            row = tk.Frame(self._top5_list, bg=BG_WHITE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"#{i+1}", font=FONT_BODY,
                     bg=BG_WHITE, fg=PRIMARY, width=3, anchor="w").pack(side="left")
            tk.Label(row, text=item["process_name"], font=FONT_BODY,
                     bg=BG_WHITE, fg=TEXT_PRIMARY, width=20, anchor="w").pack(side="left")
            tk.Label(row, text=self._format_duration(item["total_seconds"]),
                     font=FONT_BODY, bg=BG_WHITE, fg=TEXT_SECONDARY,
                     width=12, anchor="e").pack(side="right")
            tk.Label(row, text=f"{item['session_count']}次",
                     font=FONT_BODY, bg=BG_WHITE, fg=TEXT_SECONDARY,
                     width=6, anchor="e").pack(side="right")

    # ============================================================
    # 公开刷新
    # ============================================================

    def refresh(self):
        """刷新全部数据。"""
        # 卡片数据
        self.total_card.value_label.config(
            text=self._format_duration(self.db.get_today_total_seconds()))
        acts = self.db.get_today_activities()
        self.apps_card.value_label.config(
            text=f"{len(set(a['process_name'] for a in acts))} 个")
        self.focus_card.value_label.config(
            text=f"{self.db.get_focus_count_today()} 次")
        self.streak_card.value_label.config(
            text=f"{self.db.get_streak_days()} 天")

        # 周图表
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        self._chart_week_data = self.db.get_weekly_stats(week_start.isoformat())
        self._draw_week_chart(self._chart_week_data)

        # 分类饼图
        self._chart_pie_data = self.db.get_category_breakdown()
        self._draw_pie_chart(self._chart_pie_data)

        # Top5
        self._draw_top5(self.db.get_top_processes(limit=5))
