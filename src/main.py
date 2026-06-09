"""
Focus Guardian - 专注卫士 v2.0
-------------------------------
纯本地运行的系统使用统计 & 专注管控工具。
不联网，不调用任何 API，不使用外部模型。

用法：
    python src/main.py
    或双击 run.bat
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import APP_TITLE, APP_VERSION, DATA_RETENTION_DAYS


def main():
    """程序主入口。"""
    print(f"🛡️  Focus Guardian - 专注卫士  v{APP_VERSION}")
    print("=" * 45)
    print("📌 全程本地运行 | 不联网 | 无外部模型")
    print()

    # 1. 数据库
    print("📂 初始化数据库...")
    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        print("   ✅ 数据库就绪")
    except Exception as e:
        print(f"   ❌ 数据库初始化失败：{e}")
        traceback.print_exc()
        input("按回车退出...")
        return

    try:
        db.cleanup_old_data(DATA_RETENTION_DAYS)
    except Exception:
        pass

    # 2. 监控
    print("👁️  启动活动监控...")
    monitor = None
    try:
        from src.monitor.activity_monitor import ActivityMonitor
        monitor = ActivityMonitor(db)
        monitor.start()
        print("   ✅ 监控已启动")
    except Exception as e:
        print(f"   ⚠️ 监控启动失败：{e}（将以仅查看模式运行）")

    # 3. 专注管理器
    print("🍅 初始化专注管理器...")
    focus_mgr = None
    try:
        from src.focus.focus_manager import FocusManager
        focus_mgr = FocusManager(db)
        print("   ✅ 番茄钟就绪")
    except Exception as e:
        print(f"   ⚠️ 专注管理器启动失败：{e}")

    # 4. UI
    print("🖥️  启动界面...")
    try:
        from src.ui.main_window import MainWindow
        window = MainWindow(db, monitor, focus_mgr)
        print("   ✅ 窗口已创建")
    except Exception as e:
        print(f"   ❌ 窗口创建失败：{e}")
        traceback.print_exc()
        if monitor: monitor.stop()
        input("按回车退出...")
        return

    print()
    print("=" * 45)
    print("👋 关闭窗口 = 缩到托盘，右键托盘可退出")
    print("=" * 45)
    print()

    try:
        window.run()
    except KeyboardInterrupt:
        print("\n⚠️ 中断信号")
    except Exception as e:
        print(f"\n❌ {e}")
        traceback.print_exc()
    finally:
        if monitor: monitor.stop()
        print("👋 已退出")


if __name__ == "__main__":
    main()
