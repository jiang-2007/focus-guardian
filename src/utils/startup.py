"""
开机自启管理模块
-----------------
通过 Windows 注册表 Run 键管理开机自启。
"""

import os
import sys

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

# 注册表键路径
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "FocusGuardian"


def get_startup_script_path() -> str:
    """
    获取开机启动时要运行的脚本路径。
    返回 run.bat 的完整路径。
    """
    # 假设 run.bat 在项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(project_root, "run.bat")


def is_startup_enabled() -> bool:
    """
    检查是否已设置开机自启。

    返回:
        True = 已启用开机自启
        False = 未启用
    """
    if not HAS_WINREG:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, REG_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


def enable_startup():
    """
    启用开机自启。
    将程序添加到 Windows 注册表 Run 键。
    """
    if not HAS_WINREG:
        print("⚠️ 无法访问 Windows 注册表")
        return False

    try:
        script_path = get_startup_script_path()

        # 如果 run.bat 不存在，创建它
        if not os.path.exists(script_path):
            _create_run_bat(script_path)

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, script_path)
        winreg.CloseKey(key)

        print("✅ 已启用开机自启")
        return True
    except Exception as e:
        print(f"❌ 启用开机自启失败：{e}")
        return False


def disable_startup():
    """
    禁用开机自启。
    从 Windows 注册表 Run 键中移除程序。
    """
    if not HAS_WINREG:
        print("⚠️ 无法访问 Windows 注册表")
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH, 0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )

        # 检查值是否存在
        try:
            winreg.QueryValueEx(key, REG_NAME)
            winreg.DeleteValue(key, REG_NAME)
        except FileNotFoundError:
            pass  # 本来就没有，不需要删

        winreg.CloseKey(key)
        print("✅ 已禁用开机自启")
        return True
    except Exception as e:
        print(f"❌ 禁用开机自启失败：{e}")
        return False


def _create_run_bat(script_path: str):
    """
    创建启动脚本 run.bat。

    内容：用 Python 启动 main.py，后台运行不显示命令行窗口。
    """
    python_exe = sys.executable
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    main_py = os.path.join(project_dir, "src", "main.py")

    content = f'''@echo off
REM Focus Guardian 启动脚本
REM 静默启动，不显示命令行窗口

cd /d "{project_dir}"
start "" /B "{python_exe}" "{main_py}"
'''

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ 已创建启动脚本：{script_path}")
