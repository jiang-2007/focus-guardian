"""
设置页面 v2.0
-------------
黑/白名单管理 + 每日限额 + 番茄钟设置 + 开机自启开关 + 数据管理。
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from src.ui.styles import (
    BG_WHITE, BG_LIGHT, PRIMARY, PRIMARY_BG, PRIMARY_DARK, PRIMARY_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT, DANGER, WARNING, INFO,
    FONT_TITLE, FONT_HEADING, FONT_BODY, FONT_SMALL, CARD_PADDING
)
from src.config import (
    PRESET_ENTERTAINMENT, PRESET_WORK, PRESET_GAMES,
    POMODORO_WORK_MINUTES, POMODORO_SHORT_BREAK, POMODORO_LONG_BREAK
)


class SettingsPage(tk.Frame):
    """设置页面 v2.0。"""

    def __init__(self, parent, db_manager):
        super().__init__(parent, bg=BG_LIGHT)
        self.db = db_manager
        self._list_refreshers = []
        self._build_ui()

    def _build_ui(self):
        # 标题
        title_bar = tk.Frame(self, bg=BG_WHITE, height=60)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="⚙️ 设置", font=FONT_TITLE,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(side="left", padx=CARD_PADDING, pady=10)

        # 可滚动区域
        canvas = tk.Canvas(self, bg=BG_LIGHT, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=BG_LIGHT)

        # 创建 Canvas 窗口（使用 tag 以便调整大小）
        canvas.create_window((0, 0), window=self._scroll_frame,
                            anchor="nw", tags="inner_frame")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Canvas 大小变化时同步窗口宽度
        def _on_canvas_resize(event):
            canvas.itemconfigure("inner_frame", width=event.width)
        canvas.bind("<Configure>", _on_canvas_resize)

        # 内容大小变化时更新滚动区域
        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self._scroll_frame.bind("<Configure>", _on_frame_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ---- 黑名单 ----
        self._build_list_block("🚫 黑名单", self.db.get_blacklist,
                                self._add_black, self._rem_black,
                                "导入娱乐模板", self._import_entertainment, True)

        # ---- 白名单 ----
        self._build_list_block("✅ 白名单", self.db.get_whitelist,
                                self._add_white, self._rem_white,
                                "导入工作模板", self._import_work, True)

        # ---- 每日限额 ----
        self._build_limit_block()

        # ---- 番茄钟设置 ----
        self._build_pomodoro_block()

        # ---- 开机自启 ----
        self._build_startup_block()

        # ---- 数据管理 ----
        self._build_data_block()

    # ============================================================
    # 通用列表块
    # ============================================================

    def _build_list_block(self, title, get_fn, add_fn, rem_fn,
                          tmpl_text, tmpl_fn, show_quick_add=False):
        section = tk.Frame(self._scroll_frame, bg=BG_WHITE)
        section.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        header = tk.Frame(section, bg=BG_WHITE)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 5))
        tk.Label(header, text=title, font=FONT_HEADING,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(side="left")

        btn_row = tk.Frame(header, bg=BG_WHITE)
        btn_row.pack(side="right")
        tk.Button(btn_row, text=tmpl_text, font=FONT_SMALL,
                  bg=PRIMARY_BG, fg=PRIMARY, relief="flat", padx=8, pady=3,
                  cursor="hand2", command=tmpl_fn).pack(side="left", padx=2)
        if show_quick_add:
            tk.Button(btn_row, text="📋 从运行中", font=FONT_SMALL,
                      bg=INFO, fg="white", relief="flat", padx=8, pady=3,
                      cursor="hand2",
                      command=lambda g=get_fn, a=add_fn: self._quick_add(g, a)
                      ).pack(side="left", padx=2)
        tk.Button(btn_row, text="+ 添加", font=FONT_SMALL,
                  bg=PRIMARY, fg="white", relief="flat", padx=8, pady=3,
                  cursor="hand2", command=add_fn).pack(side="left", padx=2)

        tree_frame = tk.Frame(section, bg=BG_WHITE)
        tree_frame.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        tree = ttk.Treeview(tree_frame, columns=("name", "display"),
                            show="headings", height=5)
        tree.heading("name", text="进程名")
        tree.heading("display", text="显示名称")
        tree.column("name", width=180)
        tree.column("display", width=180)
        tree.pack(side="left", fill="x", expand=True)

        tk.Button(tree_frame, text="删除选中", font=FONT_SMALL,
                  bg=DANGER, fg="white", relief="flat", padx=8, pady=3,
                  cursor="hand2",
                  command=lambda t=tree, r=rem_fn: self._del_selected(t, r)
                  ).pack(side="right", padx=(5, 0))

        self._list_refreshers.append(
            lambda t=tree, g=get_fn: self._refresh_tree(t, g()))

    def _refresh_tree(self, tree, items):
        for row in tree.get_children():
            tree.delete(row)
        for item in items:
            tree.insert("", "end", values=(
                item.get("process_name", ""), item.get("display_name", "")))

    def _del_selected(self, tree, rem_fn):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择要删除的条目")
            return
        for s in sel:
            rem_fn(tree.item(s, "values")[0])
        self.refresh()

    def _quick_add(self, get_fn, add_fn):
        """弹出窗口让用户从当前运行的进程中快速添加。"""
        try:
            import psutil
            running = []
            for proc in psutil.process_iter(["name"]):
                try:
                    name = proc.info["name"]
                    if name and name.endswith(".exe"):
                        running.append(name)
                except Exception:
                    continue
        except ImportError:
            messagebox.showwarning("不可用", "需要安装 psutil 才能使用此功能")
            return

        existing = {item["process_name"].lower() for item in get_fn()}
        new_procs = sorted(set(running) - existing)

        if not new_procs:
            messagebox.showinfo("提示", "没有可添加的新进程")
            return

        # 弹窗选择
        top = tk.Toplevel(self, bg=BG_WHITE)
        top.title("从运行中进程添加")
        top.geometry("400x350")
        top.transient(self)
        top.grab_set()

        tk.Label(top, text="选择要添加的进程（可多选）：", font=FONT_BODY,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(padx=10, pady=10)

        frame = tk.Frame(top, bg=BG_WHITE)
        frame.pack(fill="both", expand=True, padx=10)
        lb = tk.Listbox(frame, selectmode="multiple", font=FONT_BODY, height=12)
        lb.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(frame, command=lb.yview)
        scroll.pack(side="right", fill="y")
        lb.config(yscrollcommand=scroll.set)

        for p in new_procs:
            lb.insert("end", p)

        def do_add():
            selected = [lb.get(i) for i in lb.curselection()]
            for p in selected:
                add_fn(p, p)
            top.destroy()
            self.refresh()

        tk.Button(top, text="添加选中", font=FONT_BODY,
                  bg=PRIMARY, fg="white", relief="flat", padx=15, pady=5,
                  cursor="hand2", command=do_add).pack(pady=10)

    # ============================================================
    # 黑白名单操作
    # ============================================================

    def _add_black(self, pn=None, dn=None):
        pn = pn or simpledialog.askstring("添加黑名单", "进程名（如 steam.exe）：")
        if not pn: return
        dn = dn or simpledialog.askstring("添加黑名单", "显示名称：") or pn
        self.db.add_to_blacklist(pn, dn)
        self.refresh()

    def _rem_black(self, pn): self.db.remove_from_blacklist(pn)

    def _import_entertainment(self):
        n = 0
        for item in PRESET_ENTERTAINMENT + PRESET_GAMES:
            self.db.add_to_blacklist(item["process_name"],
                                      item.get("display_name", item["process_name"]))
            n += 1
        messagebox.showinfo("完成", f"已导入 {n} 个娱乐/游戏进程")
        self.refresh()

    def _add_white(self, pn=None, dn=None):
        pn = pn or simpledialog.askstring("添加白名单", "进程名（如 code.exe）：")
        if not pn: return
        dn = dn or simpledialog.askstring("添加白名单", "显示名称：") or pn
        self.db.add_to_whitelist(pn, dn)
        self.refresh()

    def _rem_white(self, pn): self.db.remove_from_whitelist(pn)

    def _import_work(self):
        n = 0
        for item in PRESET_WORK:
            self.db.add_to_whitelist(item["process_name"],
                                      item.get("display_name", item["process_name"]))
            n += 1
        messagebox.showinfo("完成", f"已导入 {n} 个工作软件")
        self.refresh()

    # ============================================================
    # 每日限额
    # ============================================================

    def _build_limit_block(self):
        section = tk.Frame(self._scroll_frame, bg=BG_WHITE)
        section.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        header = tk.Frame(section, bg=BG_WHITE)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 5))
        tk.Label(header, text="⏰ 每日使用时长上限", font=FONT_HEADING,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(side="left")
        tk.Button(header, text="+ 添加限额", font=FONT_SMALL,
                  bg=PRIMARY, fg="white", relief="flat", padx=8, pady=3,
                  cursor="hand2", command=self._add_limit).pack(side="right")

        self._limit_frame = tk.Frame(section, bg=BG_WHITE)
        self._limit_frame.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

    def _add_limit(self):
        pn = simpledialog.askstring("添加限额", "进程名（如 chrome.exe）：")
        if not pn: return
        dn = simpledialog.askstring("添加限额", "显示名称：") or pn
        lim = simpledialog.askinteger("添加限额", "每日上限（分钟）：", minvalue=1, maxvalue=1440)
        if lim:
            self.db.set_daily_limit(pn, dn, lim)
            self.refresh()

    def _rem_limit(self, pn):
        self.db.remove_daily_limit(pn)
        self.refresh()

    def _refresh_limits(self):
        for w in self._limit_frame.winfo_children():
            w.destroy()
        limits = self.db.get_daily_limits()
        if not limits:
            tk.Label(self._limit_frame, text="暂无设置", font=FONT_SMALL,
                     bg=BG_WHITE, fg=TEXT_SECONDARY).pack(pady=5)
            return
        for l in limits:
            row = tk.Frame(self._limit_frame, bg=BG_WHITE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{l['display_name']} ({l['process_name']})",
                     font=FONT_BODY, bg=BG_WHITE, fg=TEXT_PRIMARY,
                     width=28, anchor="w").pack(side="left")
            tk.Label(row, text=f"每日上限 {l['limit_minutes']} 分钟",
                     font=FONT_BODY, bg=BG_WHITE, fg=TEXT_SECONDARY,
                     width=18).pack(side="left")
            tk.Button(row, text="删除", font=FONT_SMALL, bg=DANGER, fg="white",
                      relief="flat", padx=6, pady=2,
                      command=lambda p=l["process_name"]: self._rem_limit(p)
                      ).pack(side="right")

    # ============================================================
    # 番茄钟设置
    # ============================================================

    def _build_pomodoro_block(self):
        section = tk.Frame(self._scroll_frame, bg=BG_WHITE)
        section.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        tk.Label(section, text="🍅 番茄钟默认设置", font=FONT_HEADING,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(anchor="w",
                      padx=CARD_PADDING, pady=(CARD_PADDING, 5))

        desc = tk.Frame(section, bg=BG_WHITE)
        desc.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))
        tk.Label(desc, text=f"默认专注 {POMODORO_WORK_MINUTES} 分钟 "
                 f"| 短休息 {POMODORO_SHORT_BREAK} 分钟 "
                 f"| 长休息 {POMODORO_LONG_BREAK} 分钟 "
                 f"| 每 4 轮进入长休息",
                 font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_SECONDARY).pack(anchor="w")
        tk.Label(desc, text="* 可在专注页面选择预设类型或自定义时长",
                 font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_HINT).pack(anchor="w", pady=(3, 0))

    # ============================================================
    # 开机自启
    # ============================================================

    def _build_startup_block(self):
        section = tk.Frame(self._scroll_frame, bg=BG_WHITE)
        section.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 0))

        header = tk.Frame(section, bg=BG_WHITE)
        header.pack(fill="x", padx=CARD_PADDING, pady=(CARD_PADDING, 5))
        tk.Label(header, text="🚀 开机自启", font=FONT_HEADING,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(side="left")

        from src.utils.startup import is_startup_enabled, enable_startup, disable_startup
        self._startup_var = tk.BooleanVar(value=is_startup_enabled())

        cb = tk.Checkbutton(section, text="开机自动启动（静默后台运行）",
                             variable=self._startup_var, font=FONT_BODY,
                             bg=BG_WHITE, cursor="hand2",
                             command=lambda: enable_startup() if self._startup_var.get()
                             else disable_startup())
        cb.pack(anchor="w", padx=CARD_PADDING, pady=(0, CARD_PADDING))

    # ============================================================
    # 数据管理
    # ============================================================

    def _build_data_block(self):
        section = tk.Frame(self._scroll_frame, bg=BG_WHITE)
        section.pack(fill="x", padx=CARD_PADDING, pady=CARD_PADDING)

        tk.Label(section, text="🗄️ 数据管理", font=FONT_HEADING,
                 bg=BG_WHITE, fg=TEXT_PRIMARY).pack(anchor="w",
                      padx=CARD_PADDING, pady=(CARD_PADDING, 5))

        tk.Label(section, text="数据保留 90 天，超期自动清理。↓ 操作不可撤销。",
                 font=FONT_SMALL, bg=BG_WHITE, fg=TEXT_SECONDARY).pack(
                      anchor="w", padx=CARD_PADDING)

        btn_row = tk.Frame(section, bg=BG_WHITE)
        btn_row.pack(padx=CARD_PADDING, pady=(5, CARD_PADDING))
        tk.Button(btn_row, text="清空所有历史数据", font=FONT_SMALL,
                  bg=DANGER, fg="white", relief="flat", padx=10, pady=3,
                  cursor="hand2", command=self._clear_all).pack(side="left", padx=3)
        tk.Button(btn_row, text="重新显示新手引导", font=FONT_SMALL,
                  bg=INFO, fg="white", relief="flat", padx=10, pady=3,
                  cursor="hand2", command=self._reset_onboarding).pack(side="left", padx=3)

    def _clear_all(self):
        if messagebox.askyesno("⚠️ 危险操作", "确定要清空所有历史数据吗？\n\n此操作不可撤销！"):
            if messagebox.askyesno("再次确认", "请再次确认：要清空所有使用记录吗？"):
                self.db.delete_all_activities()
                messagebox.showinfo("完成", "所有历史数据已清空")
                self.refresh()

    def _reset_onboarding(self):
        self.db.set_setting("onboarding_done", "false")
        messagebox.showinfo("完成", "下次启动时将重新显示新手引导")

    # ============================================================
    # 公开
    # ============================================================

    def refresh(self):
        for fn in self._list_refreshers:
            fn()
        self._refresh_limits()
