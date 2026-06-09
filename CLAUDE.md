# CLAUDE.md — Focus Guardian 项目说明

> 本文件为 AI 助手提供项目背景和开发约定。每次对话开始时 AI 会读取此文件。

---

## 项目简介

**Focus Guardian（专注卫士）v2.0** — Windows 桌面生产力工具。

核心能力：
- 👁️ 自动监控活跃窗口，记录软件/网页使用时长
- 🍅 番茄钟专注模式（6 种预设类型 + 自定义）
- 🚫 专注时自动拦截黑名单软件（提醒 / 强制关闭）
- 📊 周/月数据看板（柱状图 + 饼图，Canvas 自绘）
- 📋 日/周/月报表 + TXT/CSV 导出
- ⏰ 每日限额 + 分级提醒
- 🖥️ 系统托盘后台运行 + 开机自启
- 🎓 首次启动 5 步新手引导

## 技术栈

| 项 | 选型 |
|----|------|
| 语言 | Python 3.10+ |
| UI | tkinter（内置，无额外 GUI 框架） |
| 数据库 | SQLite（内置 sqlite3） |
| 图表 | tkinter Canvas 自绘（无 matplotlib） |
| 进程检测 | psutil |
| Windows API | pywin32（窗口句柄、注册表） |
| 系统托盘 | pystray + Pillow |
| 纯本地 | 不联网，不调用任何 API / AI 模型 |

## 项目结构（v2.0）

```
focus_guardian/
├── CLAUDE.md                    ← 本文件
├── README.md                    ← 产品文档（竞品分析+设计思路）
├── requirements.txt
├── run.bat
├── docs/
│   ├── requirements.md          ← 功能需求
│   ├── dev_plan.md              ← 分步计划
│   ├── dev_log.md               ← 开发日志
│   └── packaging_guide.md       ← 打包部署指南
├── src/
│   ├── main.py                  ← 入口
│   ├── config.py                ← 全局配置（70+ 预设模板）
│   ├── database/db_manager.py    ← SQLite 管理（6 表 27 方法）
│   ├── monitor/activity_monitor.py ← 窗口检测
│   ├── focus/focus_manager.py     ← 番茄钟管理器
│   ├── ui/
│   │   ├── main_window.py        ← 主窗口框架
│   │   ├── dashboard_page.py     ← 数据看板（图表）
│   │   ├── report_page.py        ← 日/周/月报表
│   │   ├── focus_page.py         ← 番茄钟控制面板
│   │   ├── settings_page.py      ← 名单/限额/自启
│   │   ├── onboarding_wizard.py  ← 新手引导
│   │   ├── tray_icon.py          ← 系统托盘
│   │   └── styles.py             ← 全局样式
│   └── utils/
│       ├── export.py             ← TXT/CSV 导出
│       └── startup.py            ← 注册表自启
└── assets/                       ← 图标资源
```

## 开发约定

### 代码风格
- 类名：大驼峰 / 方法名：下划线 / 常量：全大写下划线
- 每个函数有 docstring（参数+返回值）
- 关键代码用中文注释解释为什么这样做

### 架构原则
- 单一职责：每个类只做一件事
- 配置集中在 `config.py`
- 线程安全：UI 更新用 `root.after()`，数据库写入加 `threading.Lock`
- 错误处理：try/except 捕获异常，给用户友好提示

### UI 约定（v2.0）
- 主色调：`#4CAF50`（淡绿色）系列
- 图表色板：7 色（CHART_COLORS）
- 字体：微软雅黑，10pt 正文，卡片式布局
- 窗口：900×650 默认，最小 700×500
- 所有页面标题栏高度统一 60px

### 测试
```bash
# 语法检查
python -m py_compile src/main.py

# 端到端（需在有 GUI 的 Windows 环境）
python src/main.py
```

## 当前开发状态

✅ v2.0.0 全部完成并测试通过（15 个文件，3839 行 Python）

待做：
- 网页 URL 级识别
- 定时专注计划（如 9:00-12:00 自动进入）
- macOS 适配
