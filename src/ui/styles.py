"""
UI 样式定义 v2.0
----------------
统一淡绿色浅色主题，协调各页面视觉风格。
"""

import tkinter as tk
from tkinter import ttk

# ============================================================
# 颜色定义（淡绿色主题）
# ============================================================

PRIMARY = "#4CAF50"          # 主色调
PRIMARY_LIGHT = "#81C784"    # 浅主色
PRIMARY_DARK = "#388E3C"     # 深主色
PRIMARY_BG = "#E8F5E9"       # 极浅绿背景

BG_WHITE = "#FFFFFF"
BG_LIGHT = "#F5F5F5"
BG_SIDEBAR = "#FAFAFA"

TEXT_PRIMARY = "#212121"
TEXT_SECONDARY = "#757575"
TEXT_HINT = "#BDBDBD"

DANGER = "#F44336"
WARNING = "#FF9800"
INFO = "#2196F3"

# 分类色
COLOR_WORK = "#4CAF50"
COLOR_NEUTRAL = "#FF9800"
COLOR_ENTERTAINMENT = "#F44336"

# 图表专用色（最多 7 色）
CHART_COLORS = ["#4CAF50", "#81C784", "#A5D6A7", "#C8E6C9",
                "#FF9800", "#F44336", "#2196F3"]

# ============================================================
# 字体定义
# ============================================================

FONT_FAMILY = "Microsoft YaHei"

FONT_TITLE   = (FONT_FAMILY, 16, "bold")
FONT_HEADING = (FONT_FAMILY, 13, "bold")
FONT_BODY    = (FONT_FAMILY, 10)
FONT_SMALL   = (FONT_FAMILY, 9)
FONT_BIG     = (FONT_FAMILY, 24, "bold")
FONT_MEGA    = (FONT_FAMILY, 52, "bold")

# ============================================================
# 尺寸定义
# ============================================================

SIDEBAR_WIDTH = 180
CARD_PADDING = 15
BUTTON_PADDING_X = 20
BUTTON_PADDING_Y = 8

# ============================================================
# ttk 样式配置
# ============================================================

def setup_styles():
    """配置 ttk 全局样式。"""
    style = ttk.Style()
    themes = style.theme_names()
    if "clam" in themes:
        style.theme_use("clam")
    elif "vista" in themes:
        style.theme_use("vista")

    # --- 按钮 ---
    style.configure("Primary.TButton", background=PRIMARY,
                    foreground="white", borderwidth=0, focuscolor="none",
                    font=FONT_BODY, padding=(BUTTON_PADDING_X, BUTTON_PADDING_Y))
    style.map("Primary.TButton",
              background=[("active", PRIMARY_DARK), ("pressed", PRIMARY_DARK)])

    style.configure("Secondary.TButton", background=BG_WHITE,
                    foreground=TEXT_PRIMARY, borderwidth=1, focuscolor="none",
                    font=FONT_BODY, padding=(BUTTON_PADDING_X, BUTTON_PADDING_Y))

    style.configure("Danger.TButton", background=DANGER,
                    foreground="white", borderwidth=0, focuscolor="none",
                    font=FONT_BODY, padding=(BUTTON_PADDING_X, BUTTON_PADDING_Y))

    # --- 标签 ---
    style.configure("Title.TLabel", font=FONT_TITLE, foreground=TEXT_PRIMARY,
                    background=BG_WHITE)
    style.configure("Heading.TLabel", font=FONT_HEADING, foreground=TEXT_PRIMARY,
                    background=BG_WHITE)
    style.configure("Body.TLabel", font=FONT_BODY, foreground=TEXT_PRIMARY,
                    background=BG_WHITE)
    style.configure("Secondary.TLabel", font=FONT_SMALL,
                    foreground=TEXT_SECONDARY, background=BG_WHITE)
    style.configure("BigNumber.TLabel", font=FONT_BIG, foreground=PRIMARY,
                    background=BG_WHITE)

    # --- Frame ---
    style.configure("Card.TFrame", background=BG_WHITE, relief="solid",
                    borderwidth=1)

    # --- Treeview ---
    style.configure("Treeview", font=FONT_BODY, rowheight=30,
                    background=BG_WHITE, fieldbackground=BG_WHITE)
    style.configure("Treeview.Heading", font=(FONT_FAMILY, 10, "bold"),
                    background=BG_LIGHT, foreground=TEXT_PRIMARY)

    # --- Progressbar ---
    style.configure("TProgressbar", troughcolor=BG_LIGHT,
                    background=PRIMARY, thickness=8)
