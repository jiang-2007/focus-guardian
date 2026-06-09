"""
全局配置文件
-----------
所有可修改的配置项集中在这里，方便统一管理。
"""

import os

# ============================================================
# 路径配置
# ============================================================

# 应用数据目录（存放数据库等）
APP_DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "FocusGuardian")

# 数据库文件路径
DB_PATH = os.path.join(APP_DATA_DIR, "data.db")

# 确保数据目录存在
os.makedirs(APP_DATA_DIR, exist_ok=True)

# ============================================================
# 监控配置
# ============================================================

# 窗口检测间隔（秒）—— 每隔多久检测一次当前活跃窗口
CHECK_INTERVAL = 1

# 最短记录时长（秒）—— 短于此时间的切换被忽略，避免碎片数据
MIN_DURATION = 3

# 空闲检测时间（秒）—— 鼠标键盘无操作超过此时间视为空闲
IDLE_TIMEOUT = 300  # 5 分钟

# ============================================================
# 数据保留
# ============================================================

# 数据保留天数（超过此天数的记录自动清理）
DATA_RETENTION_DAYS = 90

# ============================================================
# 专注模式默认值
# ============================================================

# 预设专注时长（分钟）
FOCUS_PRESETS = [25, 45, 60, 90]

# 默认专注时长（分钟）
DEFAULT_FOCUS_MINUTES = 25

# 严格模式默认值（True = 强制关闭黑名单进程，False = 仅提醒）
STRICT_MODE_DEFAULT = False

# ============================================================
# 每日限额提醒
# ============================================================

# 达到限额 80% 时提醒
LIMIT_WARN_PERCENT = 80

# 超限后再次提醒间隔（秒）
LIMIT_REMIND_INTERVAL = 600  # 10 分钟

# ============================================================
# UI 配置
# ============================================================

# 窗口标题
APP_TITLE = "Focus Guardian - 专注卫士"

# 窗口默认大小
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 650

# 窗口最小大小
WINDOW_MIN_WIDTH = 700
WINDOW_MIN_HEIGHT = 500

# ============================================================
# 预设软件分类模板
# ============================================================

# 常见娱乐类软件（黑名单模板）
PRESET_ENTERTAINMENT = [
    # 游戏平台
    {"process_name": "steam.exe", "display_name": "Steam"},
    {"process_name": "epicgameslauncher.exe", "display_name": "Epic Games"},
    {"process_name": "league of legends.exe", "display_name": "英雄联盟"},
    {"process_name": "valorant.exe", "display_name": "Valorant"},
    {"process_name": "genshinimpact.exe", "display_name": "原神"},
    {"process_name": "minecraft.exe", "display_name": "Minecraft"},
    # 视频/直播
    {"process_name": "douyu.exe", "display_name": "斗鱼直播"},
    {"process_name": "huya.exe", "display_name": "虎牙直播"},
    {"process_name": "bilibili.exe", "display_name": "哔哩哔哩"},
    {"process_name": "potplayer.exe", "display_name": "PotPlayer"},
    {"process_name": "vlc.exe", "display_name": "VLC 播放器"},
    # 社交
    {"process_name": "wechat.exe", "display_name": "微信"},
    {"process_name": "qq.exe", "display_name": "QQ"},
    {"process_name": "telegram.exe", "display_name": "Telegram"},
    {"process_name": "discord.exe", "display_name": "Discord"},
    # 购物
    {"process_name": "taobao.exe", "display_name": "淘宝"},
    {"process_name": "jd.exe", "display_name": "京东"},
]

# 常见工作类软件（白名单模板）
PRESET_WORK = [
    {"process_name": "code.exe", "display_name": "VS Code"},
    {"process_name": "devenv.exe", "display_name": "Visual Studio"},
    {"process_name": "pycharm64.exe", "display_name": "PyCharm"},
    {"process_name": "idea64.exe", "display_name": "IntelliJ IDEA"},
    {"process_name": "notepad++.exe", "display_name": "Notepad++"},
    {"process_name": "excel.exe", "display_name": "Excel"},
    {"process_name": "winword.exe", "display_name": "Word"},
    {"process_name": "powerpnt.exe", "display_name": "PowerPoint"},
    {"process_name": "obsidian.exe", "display_name": "Obsidian"},
    {"process_name": "typora.exe", "display_name": "Typora"},
    {"process_name": "figma.exe", "display_name": "Figma"},
    {"process_name": "photoshop.exe", "display_name": "Photoshop"},
]

# ============================================================
# 浏览器进程名映射
# ============================================================

BROWSER_PROCESSES = {
    "chrome.exe": "Chrome",
    "msedge.exe": "Edge",
    "firefox.exe": "Firefox",
}

# ============================================================
# 番茄钟配置
# ============================================================

# 单次专注时长（分钟）
POMODORO_WORK_MINUTES = 25

# 短休息时长（分钟）
POMODORO_SHORT_BREAK = 5

# 长休息时长（分钟）
POMODORO_LONG_BREAK = 15

# 几轮后进入长休息
POMODORO_CYCLES_BEFORE_LONG_BREAK = 4

# ============================================================
# 休息提醒配置
# ============================================================

# 休息提醒间隔（秒）—— 默认每小时提醒一次
REST_REMIND_INTERVAL = 3600

# ============================================================
# 新手引导步骤
# ============================================================

ONBOARDING_STEPS = [
    {
        "step": 1,
        "title": "欢迎使用 Focus Guardian",
        "description": "专注卫士将帮助你追踪电脑使用习惯，提升专注效率。",
    },
    {
        "step": 2,
        "title": "设置黑白名单",
        "description": "将娱乐软件加入黑名单，工作软件加入白名单，专注模式下会自动拦截黑名单程序。",
    },
    {
        "step": 3,
        "title": "开始首次专注",
        "description": "选择一个专注时长，点击开始即可进入专注模式。番茄钟默认 25 分钟工作 + 5 分钟休息。",
    },
    {
        "step": 4,
        "title": "查看使用报表",
        "description": "在报表页可以查看每日、每周的软件使用统计，了解你的时间都花在了哪里。",
    },
    {
        "step": 5,
        "title": "设置每日限额",
        "description": "为娱乐软件设置每日使用上限，超过限额会自动提醒你。",
    },
]

# ============================================================
# 应用版本号
# ============================================================

APP_VERSION = "2.0.0"

# ============================================================
# 更多预设模板 —— 常见网站进程
# ============================================================

# 常见娱乐网站（通过浏览器进程 + URL/标题关键词匹配的黑名单补充）
PRESET_ENTERTAINMENT_SITES = [
    {"site_name": "抖音", "keywords": ["douyin", "抖音"]},
    {"site_name": "快手", "keywords": ["kuaishou", "快手"]},
    {"site_name": "微博", "keywords": ["weibo", "微博"]},
    {"site_name": "知乎", "keywords": ["zhihu", "知乎"]},
    {"site_name": "小红书", "keywords": ["xiaohongshu", "小红书"]},
    {"site_name": "YouTube", "keywords": ["youtube", "youtu.be"]},
    {"site_name": "Netflix", "keywords": ["netflix"]},
    {"site_name": "Twitch", "keywords": ["twitch"]},
    {"site_name": "Reddit", "keywords": ["reddit"]},
    {"site_name": "Twitter / X", "keywords": ["twitter", "x.com"]},
    {"site_name": "Instagram", "keywords": ["instagram"]},
    {"site_name": "TikTok", "keywords": ["tiktok"]},
]

# 常见工作/学习网站（白名单补充）
PRESET_WORK_SITES = [
    {"site_name": "GitHub", "keywords": ["github"]},
    {"site_name": "Stack Overflow", "keywords": ["stackoverflow"]},
    {"site_name": "Gitee", "keywords": ["gitee"]},
    {"site_name": "CSDN", "keywords": ["csdn"]},
    {"site_name": "掘金", "keywords": ["juejin"]},
    {"site_name": "Notion", "keywords": ["notion"]},
    {"site_name": "飞书文档", "keywords": ["feishu"]},
    {"site_name": "语雀", "keywords": ["yuque"]},
    {"site_name": "Google Docs", "keywords": ["docs.google"]},
    {"site_name": "Microsoft 365", "keywords": ["office.com", "onedrive"]},
]

# 更多常见游戏进程（扩展黑名单）
PRESET_GAMES = [
    {"process_name": "csgo.exe", "display_name": "CS:GO"},
    {"process_name": "cs2.exe", "display_name": "CS2"},
    {"process_name": "dota2.exe", "display_name": "Dota 2"},
    {"process_name": "pubg.exe", "display_name": "绝地求生"},
    {"process_name": "eldenring.exe", "display_name": "艾尔登法环"},
    {"process_name": "apex.exe", "display_name": "Apex 英雄"},
    {"process_name": "r5apex.exe", "display_name": "Apex 英雄"},
    {"process_name": "overwatch.exe", "display_name": "守望先锋"},
    {"process_name": "wow.exe", "display_name": "魔兽世界"},
    {"process_name": "warcraft iii.exe", "display_name": "魔兽争霸3"},
    {"process_name": "starcraft.exe", "display_name": "星际争霸"},
    {"process_name": "hearthstone.exe", "display_name": "炉石传说"},
    {"process_name": "honkai.exe", "display_name": "崩坏系列"},
    {"process_name": "starrail.exe", "display_name": "崩坏：星穹铁道"},
    {"process_name": "wuthering.exe", "display_name": "鸣潮"},
    {"process_name": "nikke.exe", "display_name": "胜利女神：妮姬"},
    {"process_name": "arknights.exe", "display_name": "明日方舟"},
    {"process_name": "fortnite.exe", "display_name": "Fortnite"},
    {"process_name": "roblox.exe", "display_name": "Roblox"},
    {"process_name": "fifa.exe", "display_name": "FIFA"},
    {"process_name": "nba2k.exe", "display_name": "NBA 2K"},
    {"process_name": "gta5.exe", "display_name": "GTA V"},
    {"process_name": "rdr2.exe", "display_name": "荒野大镖客2"},
    {"process_name": "cyberpunk2077.exe", "display_name": "赛博朋克2077"},
    {"process_name": "baldursgate3.exe", "display_name": "博德之门3"},
    {"process_name": "worldoftanks.exe", "display_name": "坦克世界"},
    {"process_name": "warframe.exe", "display_name": "星际战甲"},
    {"process_name": "warframe.x64.exe", "display_name": "星际战甲"},
    {"process_name": "pathofexile.exe", "display_name": "流放之路"},
    {"process_name": "terraria.exe", "display_name": "泰拉瑞亚"},
    {"process_name": "stardew valley.exe", "display_name": "星露谷物语"},
    {"process_name": "osu!.exe", "display_name": "osu!"},
    {"process_name": "celeste.exe", "display_name": "Celeste"},
    {"process_name": "hollow_knight.exe", "display_name": "空洞骑士"},
    {"process_name": "deadcells.exe", "display_name": "死亡细胞"},
    {"process_name": "among us.exe", "display_name": "Among Us"},
    {"process_name": "phasmophobia.exe", "display_name": "恐鬼症"},
    {"process_name": "lethal company.exe", "display_name": "致命公司"},
    {"process_name": "palworld.exe", "display_name": "幻兽帕鲁"},
    {"process_name": "blackmythwukong.exe", "display_name": "黑神话：悟空"},
]

# ============================================================
# 专注类型列表（预设时长组合）
# ============================================================

FOCUS_TYPES = [
    {
        "type_id": "pomodoro",
        "name": "番茄钟",
        "work_minutes": 25,
        "break_minutes": 5,
        "description": "经典番茄工作法，25 分钟专注 + 5 分钟休息",
    },
    {
        "type_id": "pomodoro_long",
        "name": "长番茄钟",
        "work_minutes": 50,
        "break_minutes": 10,
        "description": "延长番茄钟，50 分钟专注 + 10 分钟休息",
    },
    {
        "type_id": "deep_work",
        "name": "深度工作",
        "work_minutes": 90,
        "break_minutes": 20,
        "description": "90 分钟深度专注，适合需要长时间沉浸的任务",
    },
    {
        "type_id": "power_hour",
        "name": "强力小时",
        "work_minutes": 60,
        "break_minutes": 10,
        "description": "60 分钟高强度专注 + 10 分钟休息",
    },
    {
        "type_id": "sprint",
        "name": "短冲刺",
        "work_minutes": 15,
        "break_minutes": 3,
        "description": "15 分钟快速冲刺，适合碎片时间利用",
    },
    {
        "type_id": "custom",
        "name": "自定义",
        "work_minutes": 0,
        "break_minutes": 0,
        "description": "自行设定专注和休息时长",
    },
]
