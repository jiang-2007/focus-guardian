# Focus Guardian 打包为 EXE 与部署指南

---

## 一、打包为单文件 EXE

### 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

### 2. 生成程序图标（可选）

准备一个 `icon.ico` 放在项目根目录 `assets/icon.ico`，或用在线工具将 PNG 转为 ICO。

### 3. 执行打包命令

在 `focus_guardian` 目录下运行：

```bash
pyinstaller --onefile --noconsole --name "FocusGuardian" --icon=assets/icon.ico --add-data "assets;assets" src/main.py
```

参数说明：
| 参数 | 含义 |
|------|------|
| `--onefile` | 打包成单个 EXE |
| `--noconsole` | 运行时不显示黑框（用 pythonw 方式启动） |
| `--name` | EXE 文件名 |
| `--icon` | 程序图标（需 .ico 格式） |
| `--add-data` | 打包额外数据文件 |

### 4. 打包完成

- 生成的 EXE 路径：`dist/FocusGuardian.exe`
- 将 EXE 复制到任意位置即可双击运行
- 首次运行会在 `%APPDATA%\FocusGuardian\` 创建数据库

### 5. 注意事项

- 部分杀毒软件可能误报 PyInstaller 打包的程序为病毒（属于 false positive）
- 可在 Windows Defender 中添加排除项
- 如需提交到杀软厂商白名单，请自行认证

---

## 二、开机自启配置

### 方法一：程序内设置（推荐）

1. 打开 Focus Guardian → 设置页
2. 勾选「开机自动启动」
3. 程序会自动写入注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`

### 方法二：手动放入启动文件夹

1. 按 `Win + R`，输入 `shell:startup`，回车
2. 将 `run.bat` 或 `FocusGuardian.exe` 的快捷方式放入该文件夹

### 方法三：任务计划程序（推荐企业环境）

1. 打开「任务计划程序」（Win + R → `taskschd.msc`）
2. 创建基本任务 → 触发器：用户登录时
3. 操作：启动程序 → 选择 EXE 路径
4. 条件：取消「仅当使用交流电源时」的勾选

---

## 三、数据文件位置

| 文件 | 路径 |
|------|------|
| 数据库 | `%APPDATA%\FocusGuardian\data.db` |
| 导出文件 | 用户自行选择保存位置 |

备份只需复制 `data.db` 文件即可。

---

## 四、卸载

1. 设置页取消「开机自启」
2. 退出托盘程序
3. 删除 EXE 文件
4. 删除数据库：删除 `%APPDATA%\FocusGuardian\` 文件夹

---

## 五、常见打包问题

**Q: 打包后运行报错 `ModuleNotFoundError`**
A: 创建 `hook-src.py` 文件，内容：
```python
from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('src')
```
打包时加 `--additional-hooks-dir=.`

**Q: 打包后托盘图标不显示**
A: 确保 Pillow 被打包进去：
```bash
pyinstaller --onefile --noconsole --hidden-import PIL --hidden-import pystray --hidden-import win32gui --hidden-import win32process --hidden-import win32api --hidden-import psutil src/main.py
```

**Q: EXE 文件太大**
A: 使用虚拟环境 + `pip install pyinstaller`，只用需要的包，避免全局环境的包被一起打包。
