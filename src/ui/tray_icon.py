"""
系统托盘图标模块
-----------------
程序关闭窗口后驻留系统托盘，右键菜单快捷操作。
"""

import threading
from PIL import Image, ImageDraw

try:
    import pystray
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False
    print("⚠️ pystray 未安装，系统托盘功能不可用。请运行: pip install pystray")


def _create_tray_image(color: str = "#4CAF50", size: int = 32) -> Image.Image:
    """
    用 Pillow 动态生成托盘图标（绿色盾牌）。

    参数:
        color: 主色调
        size: 图标尺寸（像素）
    返回:
        PIL Image 对象
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 3
    # 盾牌外形：上半三角 + 下半矩形，用圆角矩形简化
    # 画盾牌主体
    draw.rounded_rectangle(
        [margin, margin + 4, size - margin, size - margin],
        radius=4,
        fill=color
    )

    # 画小对勾（白色）
    check_color = "white"
    # 简化为一条横线 + 一条短线
    mid_y = size // 2
    draw.line(
        [margin + 4, mid_y, size // 2 - 2, size - margin - 4],
        fill=check_color, width=3
    )
    draw.line(
        [size // 2 - 2, size - margin - 4, size - margin - 4, margin + 4],
        fill=check_color, width=3
    )

    return img


def _create_active_image() -> Image.Image:
    """生成专注模式中的图标（橙色）。"""
    return _create_tray_image("#FF9800")


def _create_idle_image() -> Image.Image:
    """生成正常监控图标（绿色）。"""
    return _create_tray_image("#4CAF50")


class TrayIcon:
    """
    系统托盘图标管理器。

    用法:
        tray = TrayIcon(app)
        tray.show()
    """

    def __init__(self, app):
        """
        初始化托盘图标。

        参数:
            app: 主应用对象，需要提供以下方法：
                 - app.show_window()  显示主窗口
                 - app.quit_app()     退出程序
                 - app.toggle_focus() 切换专注模式
        """
        if not HAS_PYSTRAY:
            self._tray = None
            return

        self._app = app
        self._tray = None
        self._menu_items = {}

    def show(self):
        """显示托盘图标。"""
        if not HAS_PYSTRAY:
            return

        if self._tray is not None:
            return  # 已经存在

        # 创建菜单
        menu = self._build_menu()

        # 创建托盘图标
        icon_image = _create_idle_image()
        self._tray = pystray.Icon(
            name="FocusGuardian",
            icon=icon_image,
            title="Focus Guardian - 专注卫士",
            menu=menu
        )

        # 在后台线程运行托盘
        tray_thread = threading.Thread(
            target=self._tray.run,
            daemon=True,
            name="TrayIcon"
        )
        tray_thread.start()

        print("🖥️  系统托盘已启动")

    def _build_menu(self):
        """构建托盘右键菜单。"""
        menu = (
            pystray.MenuItem("打开面板", self._on_show_window, default=True),
            pystray.MenuItem("开始专注", self._on_toggle_focus),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出程序", self._on_quit),
        )
        return menu

    def set_focus_mode(self, active: bool):
        """切换托盘图标（专注模式 vs 普通模式）。"""
        if not HAS_PYSTRAY or self._tray is None:
            return

        if active:
            self._tray.icon = _create_active_image()
            # 更新菜单文字
            self._tray.title = "Focus Guardian - 专注中..."
        else:
            self._tray.icon = _create_idle_image()
            self._tray.title = "Focus Guardian - 专注卫士"

    def stop(self):
        """停止托盘图标。"""
        if not HAS_PYSTRAY or self._tray is None:
            return

        self._tray.stop()
        self._tray = None
        print("🛑 系统托盘已退出")

    # ================================================================
    # 菜单回调
    # ================================================================

    def _on_show_window(self, icon, item):
        """显示主窗口。"""
        self._app.show_window()

    def _on_toggle_focus(self, icon, item):
        """切换专注模式。"""
        self._app.toggle_focus()

    def _on_quit(self, icon, item):
        """退出程序。"""
        self.stop()
        self._app.quit_app()
