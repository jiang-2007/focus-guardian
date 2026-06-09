"""
主窗口 v2.0
-----------
应用主窗口 + 侧边栏导航 + 新手引导 + 系统托盘集成。
"""

import tkinter as tk
from tkinter import ttk, messagebox
import traceback

from src.config import APP_TITLE, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT
from src.ui.styles import (
    BG_WHITE, BG_LIGHT, BG_SIDEBAR, PRIMARY, PRIMARY_BG, PRIMARY_DARK,
    TEXT_PRIMARY, TEXT_SECONDARY,
    FONT_TITLE, FONT_BODY, FONT_SMALL, SIDEBAR_WIDTH, setup_styles
)
from src.ui.dashboard_page import DashboardPage
from src.ui.report_page import ReportPage
from src.ui.focus_page import FocusPage
from src.ui.settings_page import SettingsPage
from src.ui.tray_icon import TrayIcon


class MainWindow:
    """应用程序主窗口。"""

    def __init__(self, db_manager, activity_monitor, focus_manager):
        self.db = db_manager
        self.monitor = activity_monitor
        self.focus = focus_manager
        self._tray = None
        self._quitting = False

        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG_LIGHT)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 必须在创建 widget 之前调用
        setup_styles()

        self._current_nav = None
        self._nav_buttons = {}

        # 构建 UI
        self._build_sidebar()
        self._build_content()

        # 先强制一次布局，让所有 widget 获得真实尺寸
        self.root.update_idletasks()
        self.root.update()

        # 默认显示仪表盘
        self._show_page("dashboard")

        # 立即刷新一次（不等 5 秒）
        self._do_refresh()

        # 定时刷新
        self._schedule_refresh()

        # 延迟检查新手引导
        self.root.after(800, self._check_onboarding)

    # ============================================================
    # 侧边栏
    # ============================================================

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        logo_frame.pack(fill="x", pady=(20, 25))

        tk.Label(logo_frame, text="🛡️", font=("Microsoft YaHei", 28),
                 bg=BG_SIDEBAR).pack()
        tk.Label(logo_frame, text="专注卫士", font=FONT_TITLE,
                 bg=BG_SIDEBAR, fg=PRIMARY_DARK).pack()
        tk.Label(logo_frame, text="Focus Guardian",
                 font=("Microsoft YaHei", 8), bg=BG_SIDEBAR,
                 fg=TEXT_SECONDARY).pack()

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=15)

        nav_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        nav_frame.pack(fill="x", pady=15, padx=10)

        nav_items = [
            ("dashboard", "📊  仪表盘"),
            ("report",    "📋  报表"),
            ("focus",     "🍅  专注"),
            ("settings",  "⚙️  设置"),
        ]

        for key, label in nav_items:
            # 用默认参数闭包捕获当前 key 值
            btn = tk.Button(nav_frame, text=label, font=FONT_BODY,
                            bg=BG_SIDEBAR, fg=TEXT_PRIMARY, relief="flat",
                            anchor="w", padx=15, pady=10, cursor="hand2",
                            command=lambda k=key: self._show_page(k))
            btn.pack(fill="x", pady=2)
            self._nav_buttons[key] = btn

        # 版本号
        tk.Label(sidebar, text=f"v{APP_VERSION}", font=FONT_SMALL,
                 bg=BG_SIDEBAR, fg=TEXT_SECONDARY).pack(side="bottom", pady=10)

    # ============================================================
    # 内容区域
    # ============================================================

    def _build_content(self):
        self.content_frame = tk.Frame(self.root, bg=BG_LIGHT)
        self.content_frame.pack(side="right", fill="both", expand=True)

        self.pages = {
            "dashboard": DashboardPage(self.content_frame, self.db),
            "report":    ReportPage(self.content_frame, self.db),
            "focus":     FocusPage(self.content_frame, self.focus, self.db),
            "settings":  SettingsPage(self.content_frame, self.db),
        }

    def _show_page(self, page_key: str):
        """切换页面。"""
        try:
            # 更新导航按钮高亮
            if self._current_nav and self._current_nav in self._nav_buttons:
                self._nav_buttons[self._current_nav].config(
                    bg=BG_SIDEBAR, fg=TEXT_PRIMARY)

            if page_key in self._nav_buttons:
                self._nav_buttons[page_key].config(
                    bg=PRIMARY_BG, fg=PRIMARY_DARK)

            self._current_nav = page_key

            # 隐藏所有页面
            for page in self.pages.values():
                page.pack_forget()

            # 显示目标页面
            target = self.pages[page_key]
            target.pack(fill="both", expand=True)

            # 强制布局
            self.root.update_idletasks()

            # 刷新页面数据
            if hasattr(target, "refresh"):
                target.refresh()
        except Exception as e:
            print(f"[ERROR] 页面切换失败 ({page_key}): {e}")
            traceback.print_exc()

    # ============================================================
    # 刷新
    # ============================================================

    def _do_refresh(self):
        """立即刷新当前页面。"""
        if self._current_nav and self._current_nav in self.pages:
            page = self.pages[self._current_nav]
            if hasattr(page, "refresh"):
                try:
                    page.refresh()
                except Exception as e:
                    print(f"[WARN] 刷新失败 ({self._current_nav}): {e}")

    def _schedule_refresh(self):
        """定时刷新。"""
        self._do_refresh()
        self.root.after(5000, self._schedule_refresh)

    # ============================================================
    # 新手引导
    # ============================================================

    def _check_onboarding(self):
        """检查是否需要显示新手引导。"""
        try:
            if not self.db.is_onboarding_done():
                from src.ui.onboarding_wizard import OnboardingWizard
                OnboardingWizard(self.root, self.db, on_complete=None).show()
        except Exception as e:
            print(f"[WARN] 新手引导失败: {e}")

    # ============================================================
    # 窗口管理
    # ============================================================

    def _on_close(self):
        """关闭窗口 → 最小化到托盘（如可用），否则确认退出。"""
        if HAS_TRAY():
            self.hide_window()
        else:
            if messagebox.askyesno("确认退出", "确定要退出 Focus Guardian 吗？"):
                self.quit_app()

    def show_window(self):
        """恢复窗口。"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self._do_refresh()

    def hide_window(self):
        """隐藏到托盘。"""
        self.root.withdraw()
        try:
            self._ensure_tray()
        except Exception:
            pass

    def toggle_focus(self):
        """托盘菜单 → 打开专注页。"""
        self.show_window()
        self._show_page("focus")

    def quit_app(self):
        """完全退出。"""
        if self._quitting:
            return
        self._quitting = True
        try:
            if self.monitor:
                self.monitor.stop()
        except Exception:
            pass
        try:
            if self._tray is not None:
                self._tray.stop()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    # ============================================================
    # 托盘
    # ============================================================

    def _ensure_tray(self):
        if self._tray is None:
            self._tray = TrayIcon(self)
            self._tray.show()

    def run(self):
        """进入主事件循环。"""
        self._ensure_tray()
        self.root.mainloop()


def HAS_TRAY() -> bool:
    try:
        import pystray
        return True
    except ImportError:
        return False
