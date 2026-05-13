# 🎵 抖音音乐开放平台 · AI 自动化工作流 — Hermes → Hermes 部署手册

> **写给另一个 Hermes Agent 阅读**：本文档是一份完整的可执行指引。
> 按顺序执行每一个 Step，每步末尾有验证点，确认通过后再继续下一步。
> 如果某一步遇到错误，跳到末尾的「踩坑记录」对照解决。

---

## 项目概述

自动化 AI 音乐创作系统，从热搜分析 → AI 作词/作曲 → 编辑器导出到资产页。

```
热搜分析(抖音音乐平台)
  → 选题Agent(市场趋势报告)
  → 创意总监Agent(歌曲蓝图)
  → 词曲创作Agent(歌词 + 作曲提示)
  → BrowserCore(DrissionPage 浏览器操控)
    → AI作曲页 → 生成音乐素材
    → AI编辑器 → 导出到「我的资产」页 🏁
```

**流程终点**：歌曲导出到资产页。发布全曲由用户在浏览器手动操作。

项目目录：`~/.hermes/auto-douyinmusic/`

---

## 架构速览

```
~/.hermes/auto-douyinmusic/
├── main.py                     # CLI入口
├── config.yaml                 # 全局配置 + 租户定义
├── requirements.txt            # Python依赖
├── .env                        # API Key（DeepSeek）
├── .gitignore
│
├── infrastructure/
│   ├── browser.py              # BrowserCore — DrissionPage封装
│   ├── llm_client.py           # LLMClient — DeepSeek API调用
│   └── platform/               # 平台适配（预留）
│
├── models/
│   ├── config.py               # 配置加载（YAML + .env）
│   └── song.py                 # 歌曲数据模型
│
├── pipelines/
│   ├── base.py                 # BasePipeline
│   └── music_creation.py       # 音乐创作Pipeline
│
├── services/
│   ├── agents/                 # Agent层（orchestrator/collector/creative/songwriter）
│   ├── collector_service.py    # 热搜采集
│   ├── composition_service.py  # 作曲（浏览器操作）
│   ├── lyrics_service.py       # 歌词生成（LLM）
│   └── editor_service.py       # 编辑器操作
│
├── export_v5.py                # 🔑 单曲导出（DrissionPage，生产级）
├── compose_cdp.py              # 🎵 CDP 直连作曲（灵感/高级模式）
├── export_cdp.py               # 🧪 CDP 直连导出（WebSocket，试验中）
├── douyinmusic_opencli.py      # OpenCLI 桥接作曲（备选）
├── opencli_bridge.py           # OpenCLI 子进程桥接
├── check_assets.py             # 资产页验证
├── start_chrome.sh             # Chrome启动脚本
├── 项目记忆.md                  # 完整踩坑记录
│
├── archive/                    # 📦 119个废弃版本文件
├── data/
│   └── douyin_music/default/
│       └── chrome_data/        # Chrome用户数据（登录态持久化）
└── notes/                      # 踩坑笔记
```

---

## Step 0 — 准备项目文件

从源机器复制整个项目目录（排除 `data/`、`.venv/`、`.env`）：

```bash
# 在源机器上
cd ~/.hermes
tar czf auto-douyinmusic.tar.gz auto-douyinmusic \
  --exclude='auto-douyinmusic/data' \
  --exclude='auto-douyinmusic/.venv' \
  --exclude='auto-douyinmusic/.env'

# 传到新机器（scp/rsync/U盘/微信文件助手等）
# scp auto-douyinmusic.tar.gz new-machine:~/.hermes/

# 在新机器上解压
cd ~/.hermes
tar xzf auto-douyinmusic.tar.gz
cd auto-douyinmusic
```

> ⚠️ 不要复制 `.venv/` 和 `data/` 目录，每台机器独立创建。
> ⚠️ `.env` 文件包含 API Key，不要复制，手动创建。

---

## Step 1 — 安装 Python 依赖

```bash
cd ~/.hermes/auto-douyinmusic

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖（国内用清华镜像加速）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
  DrissionPage websocket-client requests pyyaml pydantic loguru openai python-dotenv
```

**验证：**
```bash
source .venv/bin/activate
python3 -c "
import DrissionPage, websocket, requests, yaml, pydantic, loguru, openai, dotenv
print('✅ 所有依赖安装成功')
"
```

---

## Step 2 — 配置 DeepSeek API Key

工作流使用 DeepSeek 作为 AI 模型。创建 `.env` 文件：

```bash
cd ~/.hermes/auto-douyinmusic

cat > .env << 'EOF'
DEEPSEEK_API_KEY="sk-你的DeepSeek API Key"
DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
EOF
```

> DeepSeek API Key 获取：https://platform.deepseek.com → 注册 → 创建 API Key
> 模型使用：主控 Agent 用 `deepseek-v4-pro`，子 Agent 用 `deepseek-chat`

**验证：**
```bash
source .venv/bin/activate
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('DEEPSEEK_API_KEY', '')
print(f'✅ API Key 已配置 (长度: {len(key)})' if key else '❌ 未找到 DEEPSEEK_API_KEY')
"
```

---

## Step 3 — 启动 Chrome（带远程调试端口）

工作流通过 **DrissionPage** 连接 Chrome，操控抖音音乐开放平台的网页元素。

Chrome **必须手动启动**（不能依赖 DrissionPage 自动启动），否则登录态丢失。

```bash
cd ~/.hermes/auto-douyinmusic

# 创建用户数据目录
CHROME_DATA="$HOME/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data"
mkdir -p "$CHROME_DATA"

# 清理锁文件（如果之前 Chrome 异常退出）
rm -f "$CHROME_DATA/SingletonLock" "$CHROME_DATA/SingletonSocket" 2>/dev/null

# 杀掉冲突的 Chrome 实例
pkill -f "Google Chrome.*9223" 2>/dev/null
sleep 2

# 启动 Chrome（窗口隐藏模式，不是 --headless）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9223 \
  --remote-allow-origins="*" \
  --user-data-dir="$CHROME_DATA" \
  --window-position=-32000,-32000 \
  --window-size=1,1 \
  --no-first-run \
  --disable-popup-blocking \
  --hide-crash-restore-bubble \
  --disable-infobars \
  --no-default-browser-check \
  2>&1 &
```

> ⚠️ **为什么不能 `--headless`？** Chrome 147+ 的 `--headless=new` 兼容性问题会导致 DrissionPage WebSocket 404 错误。
> 用 `--window-position=-32000,-32000` 代替，等效隐藏但 WebSocket 正常。
> ⚠️ **为什么必须手动启动？** 如果 DrissionPage 自动启动 Chrome，会用临时目录，之前登录的 Session 全部丢失。

**验证 Chrome 启动成功：**
```bash
sleep 3
curl -s http://localhost:9223/json/version | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'✅ Chrome {d[\"Browser\"]}')
print(f'✅ WebSocket: {d[\"webSocketDebuggerUrl\"][:50]}...')
"
```

---

## Step 4 — 首次登录（只需一次）

Chrome 启动后，登录抖音音乐开放平台，Session 自动持久化到 `chrome_data/`。

### 方式一：手机验证码登录（推荐）

```bash
cd ~/.hermes/auto-douyinmusic
source .venv/bin/activate

python3 << 'PYEOF'
from DrissionPage import ChromiumPage
import time

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
P.get("https://music.douyin.com/studio/create")
time.sleep(3)

# 检查是否已登录
if "login" not in P.url.lower():
    print("✅ 已登录，无需重复操作")
else:
    print("请在浏览器窗口中操作登录：")
    print("1. 点「登录」按钮")
    print("2. 切换到「验证码登录」tab")
    print("3. 输入手机号 → 获取验证码 → 输入验证码 → 登录")
    print()
    for i in range(120, 0, -1):
        time.sleep(1)
        P.get("https://music.douyin.com/studio/create")
        if "login" not in P.url.lower():
            print(f"✅ 登录成功！({120-i}秒)")
            break
        if i % 15 == 0:
            print(f"⏳ 等待登录中 ({i}秒)...")
    else:
        print("⚠️ 等待超时，可手动完成后重试")
PYEOF
```

### 方式二：二维码扫码登录

如果验证码登录遇到滑块验证码，改用二维码：

```bash
python3 << 'PYEOF'
from DrissionPage import ChromiumPage
import time, base64

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
P.get("https://music.douyin.com/studio/create")
time.sleep(3)

# 提取二维码
qr = P.run_js("""
let imgs = document.querySelectorAll('img');
for (let i of imgs) {
    if (i.alt === '二维码') {
        return i.src;
    }
}
return null;
""")
if qr and qr.startswith('data:image'):
    _, b64 = qr.split(',', 1)
    with open('/tmp/douyin_qr.png', 'wb') as f:
        f.write(base64.b64decode(b64))
    import subprocess
    subprocess.run(['open', '/tmp/douyin_qr.png'])
    print("二维码已打开，用抖音APP扫码")
else:
    print("未找到二维码，尝试手动在浏览器中扫码")
PYEOF
```

> **为什么只需一次？** Chrome 用户数据目录（`chrome_data/`）会持久化登录态。
> 以后每次启动 Chrome 用同一个 `--user-data-dir`，登录态自动恢复。
> Session 有效期约 5-10 分钟空闲后过期，已登录状态可维持数小时。

---

## Step 5 — 运行导出（核心操作）

工作流的终点是**歌曲导出到资产页**。运行方式有两种：

### 完整工作流（热搜 → 词曲 → 导出）

```bash
cd ~/.hermes/auto-douyinmusic
source .venv/bin/activate
python main.py --full --tenant douyin_music_default
```

### 单曲导出（最常用）

```bash
cd ~/.hermes/auto-douyinmusic
source .venv/bin/activate

# 前提：Chrome 9223 已启动且已登录
python export_v5.py "歌曲名"
```

#### 7 步导出流程

```
作曲页(/studio/create)
  Step 1 → 点击素材列表中的歌曲（libraryItemWrapper）
  Step 2 → 点击「AI 编辑」按钮（aiEditButton）
  Step 3 → 点击「去 AI 编辑器」按钮（primaryBtn）
  Step 4 → 进入编辑器(/studio/playground)，等歌曲加载 5-8s
  Step 5 → 点击「导出」按钮（semi-button-secondary + 三重事件链）
  Step 6 → 弹窗中改歌名 → 确认导出
  Step 7 → 验证资产页出现歌曲名
```

#### 关键选择器

| 步骤 | 选择器 | 类名（实测） |
|------|--------|-------------|
| 素材列表 | `//div[contains(@class,"libraryItemWrapper") and contains(.,"歌名")]` | `libraryItemWrapper-QRMdov` |
| AI 编辑 | `button[class*="aiEditButton"]` | `aiEditButton-BxDygS` |
| 去 AI 编辑器 | `button[class*="primaryBtn"]` | `primaryBtn-gl7Q_G` |
| 导出按钮 | `button.semi-button-secondary` (text="导出") | `semi-button-secondary` |
| 确认导出 | `button.semi-button-primary` | — |
| 歌名input | `querySelectorAll('input')` (value="新项目") | Semi UI 组件 |

---

## Step 6 — 发布全曲（人工操作 👤）

歌曲导出到资产页后，发布流程由用户在浏览器手动完成：

1. 打开 `https://music.douyin.com/studio/assets/creation`
2. 找到歌曲，点「发行全曲」
3. 选曲 → 签约 → 发布

> 自动化发布流程已废弃，原因：涉及手机验证码签署协议、滑块验证码、多步骤确认，人工操作更可靠。

---

## 常用命令

```bash
# 启动Chrome（后台）
cd ~/.hermes/auto-douyinmusic && bash start_chrome.sh

# 导出单曲
cd ~/.hermes/auto-douyinmusic && source .venv/bin/activate && python export_v5.py "歌曲名"

# 检查资产页
cd ~/.hermes/auto-douyinmusic && source .venv/bin/activate && python check_assets.py

# 查看端口占用
lsof -ti :9223

# 杀Chrome进程
lsof -ti :9223 | xargs kill -9
```

---

## 踩坑记录

完整记录见 `项目记忆.md`。以下为核心坑点摘要：

### 🔥 1. `--headless=new` → WebSocket 404
Chrome 147+ 不兼容。**必须用窗口隐藏模式**（`--window-position=-32000,-32000`）。

### 🔥 2. DrissionPage 自动启动 Chrome 丢 Session
`ChromiumPage('127.0.0.1:9223')` 端口无 Chrome 时会静默启动到临时目录。
**解决**：先手动 `bash start_chrome.sh`，等 2-3s 再连。

### 🔥 3. 导出按钮点不动
Semi UI 按钮结构是 `<button>→<span>导出</span>`，点 span 无效。
**解决**：点 `<button>` 本身，用 `mousedown+mouseup+click` 三重事件。

### 🔥 4. 歌名变 `[object HTMLInputElement]`
导出弹窗 input 默认 `disabled`，直接设值异常。
**解决**：先 `inp.disabled = false; removeAttribute('disabled')`，再用 nativeSetter。

### 🔥 5. React 输入框不认 browser_type
`<textarea>` 和 `<input>` 是 React 受控组件，browser_type 无效。
**解决**：用 `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set` + `dispatchEvent(new Event('input', {bubbles:true}))`

### 🔥 6. 批量导出时 for 循环杀不干净
Shell for 循环被杀后 Python 子进程成孤儿进程。
**解决**：逐首导出，`export_v5.py` 内置 SIGTERM 信号处理自动杀 Chrome。

---

## 多项目端口隔离

| 端口 | 项目 | 用途 |
|------|------|------|
| 9222 | 头条新闻工作流 | Chrome CDP 发布 |
| 9223 | 抖音音乐工作流 | DrissionPage 浏览器操控 |

两项目可同时运行，互不干扰。

---

## 首次部署检查清单

- [ ] Step 1: `python3 -c "import DrissionPage"` 不报错
- [ ] Step 2: `DEEPSEEK_API_KEY` 已配置且可连接
- [ ] Step 3: `curl -s http://localhost:9223/json/version` 返回 Chrome 信息
- [ ] Step 4: DrissionPage 能访问 `music.douyin.com/studio` 且已登录
- [ ] Step 5: `python export_v5.py "歌名"` 能走完 7 步导出流程

---

## 许可证

MIT
