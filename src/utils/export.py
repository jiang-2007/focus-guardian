"""
数据导出模块
-------------
支持将活动记录导出为 TXT 或 CSV 格式。
"""

import csv
from datetime import datetime


def _format_duration(seconds: int) -> str:
    """格式化时长为可读字符串。"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        return f"{seconds // 60}分钟"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}小时{m}分钟"


def export_activities(activities: list, file_path: str, fmt: str = "txt"):
    """
    将活动记录导出到文件。

    参数:
        activities: 活动记录列表（由 db_manager 返回的字典列表）
        file_path: 导出文件路径
        fmt: 格式，"txt" 或 "csv"
    """
    if fmt == "csv":
        _export_csv(activities, file_path)
    else:
        _export_txt(activities, file_path)


def _export_txt(activities: list, file_path: str):
    """
    导出为格式化的文本文件。

    输出格式:
        时间范围          | 程序名              | 时长
        08:30 ~ 09:15    | Code.exe           | 45分钟
    """
    with open(file_path, "w", encoding="utf-8") as f:
        # 标题
        today = datetime.now().strftime("%Y年%m月%d日")
        f.write(f"Focus Guardian - 使用记录报告\n")
        f.write(f"日期：{today}\n")
        f.write(f"记录数：{len(activities)} 条\n")
        f.write("=" * 65 + "\n\n")

        if not activities:
            f.write("当天无使用记录。\n")
            return

        # 表头
        f.write(f"{'时间段':<22} {'程序':<20} {'时长':>10}\n")
        f.write("-" * 65 + "\n")

        # 逐条记录（按时间升序排列）
        total_seconds = 0
        for a in sorted(activities, key=lambda x: x["start_time"]):
            start = a["start_time"][11:16] if a["start_time"] else "?"
            end = a.get("end_time", "") or ""
            end = end[11:16] if end else "?"
            time_range = f"{start} ~ {end}"

            process = a["process_name"][:20]
            duration = a.get("duration", 0)
            total_seconds += duration
            dur_str = _format_duration(duration)

            f.write(f"{time_range:<22} {process:<20} {dur_str:>10}\n")

        # 汇总
        f.write("-" * 65 + "\n")
        f.write(f"{'总计':<42} {_format_duration(total_seconds):>10}\n")

    print(f"✅ 已导出 TXT：{file_path}")


def _export_csv(activities: list, file_path: str):
    """
    导出为 CSV 格式（可用 Excel 打开）。

    CSV 列：
        日期, 开始时间, 结束时间, 进程名, 窗口标题, 时长(秒), 时长(可读)
    """
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)

        # 表头
        writer.writerow([
            "日期", "开始时间", "结束时间", "进程名",
            "窗口标题", "时长(秒)", "时长(可读)"
        ])

        # 数据行
        for a in sorted(activities, key=lambda x: x["start_time"]):
            writer.writerow([
                a.get("date", ""),
                a.get("start_time", ""),
                a.get("end_time", ""),
                a.get("process_name", ""),
                a.get("window_title", ""),
                a.get("duration", 0),
                _format_duration(a.get("duration", 0)),
            ])

    print(f"✅ 已导出 CSV：{file_path}")
