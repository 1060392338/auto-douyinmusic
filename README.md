# 🎵 抖音音乐开放平台 · AI 自动化工作流

> 从 AI 作词 → AI 作曲 → 编辑器导出 → 发布全曲，全流程自动化。
> 基于 **5-Agent 架构**（DeepSeek 双模型）+ **浏览器自动化**（DrissionPage）。

---

## 目录

- [架构概览](#架构概览)
- [功能状态](#功能状态)
- [快速开始](#快速开始)
- [CLI 使用](#cli-使用)
- [单曲导出](#单曲导出)
- [项目结构](#项目结构)
- [Agent 架构详解](#agent-架构详解)
- [已知问题 & 踩坑记录](#已知问题--踩坑记录)
- [开发指南](#开发指南)

---

## 架构概览

```
┌─────────────────────────────────────────────────┐
│                   main.py (CLI)                  │
├─────────────────────────────────────────────────┤
│                MusicCreationPipeline              │
├─────────────────────────────────────────────────┤
│              OrchestratorAgent (V4 Pro)           │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ │
│  │Collector │ │Creative  │ │Song-   │ │Pub-  │ │
│  │&Analyst  │ │Director  │ │writer  │ │lisher│ │
│  │(chat)    │ │(chat)    │ │(chat)  │ │(chat)│ │
│  └──────────┘ └──────────┘ └────────┘ └──────┘ │
├─────────────────────────────────────────────────┤
│         BrowserCore / DrissionPage (9223)         │
│     ┌──────────────┐  ┌──────────────────┐       │
│     │  Chrome 无头  │  │  抖音音乐开放平台  │       │
│     └──────────────┘  └──────────────────┘       │
└─────────────────────────────────────────────────┘
```

| 组件 | 模型 | 角色 |
|------|------|------|
| **OrchestratorAgent** | `deepseek-v4-pro` | AI 音乐制作人，统筹全局、质量门禁 |
| **CollectorAnalystAgent** | `deepseek-chat` | 热搜分析，识别热门风格方向 |
| **CreativeDirectorAgent** | `deepseek-chat` | 创意总监，生成歌曲蓝图 |
| **SongwriterAgent** | `deepseek-chat` | 词曲创作，生成歌词与作曲提示 |
| **PublisherAgent** | `deepseek-chat` | 发布全曲，管理发行签约 |

---

## 功能状态

| 功能 | 状态 | 说明 |
|------|------|------|
| ✅ AI 作词 | 已完成 | 自动生成结构化歌词（Verse-Chorus-Bridge） |
| ✅ AI 作曲（高级） | 已完成 | 风格描述 + 结构化歌词生成音乐素材 |
| ✅ 编辑器导出 | **已验证稳定** | 7 步流程导出到「我的资产」（见下方） |
| 🚧 发布全曲 | 半自动 | 选曲→签约→发布，需用户协助验证码 |
| ✅ 浏览器 Session 持久化 | 已完成 | Chrome 用户数据目录复用登录态 |
| ✅ 多 Agent 协同 | 已完成 | 双模型异构，子 Agent 用 chat 省成本 |

### 导出状态（当前进度 6/12）

| 歌曲 | 导出 | 资产页 |
|------|------|--------|
| 纸鸢远 | ✅ | 发行全曲 ✅ |
| 夏蝉语 | ✅ | 发行全曲 ✅ |
| 迷音 | ✅ | 发行全曲 ✅ |
| 巷尾琴音 | ✅ | 发行全曲 ✅ |
| 木吉他叙旧 | ✅ | 发行全曲 ✅ |
| 吉他与诗 | ✅ | 发行全曲 ✅ |
| 缓歌寄意 | ❌ 旧版导出 | 歌名错误，无发行按钮 |
| 杂乱思绪 | ❌ 未导出 | — |
| 无章 | ❌ 未导出 | — |
| 无序歌 | ❌ 未导出 | — |
| 星落肩头 | ❌ 未导出 | — |
| 空白页 | ❌ 未导出 | — |

---

## 快速开始

### 前置条件

- Python 3.10+
- macOS 系统（已适配 Chrome 路径）
- Google Chrome 浏览器
- 抖音音乐开放平台账号（[music.douyin.com](https://music.douyin.com)）

### 环境安装

```bash
# 1. 克隆仓库
git clone <repo-url> ~/.hermes/auto-douyinmusic
cd ~/.hermes/auto-douyinmusic

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY
```

### .env 配置

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

### 启动 Chrome

```bash
# 无头模式（推荐，不显示窗口）
bash start_chrome.sh

# 等价于：
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="/Users/mac/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data" \
  --remote-allow-origins="*" \
  --window-position=-32000,-32000 \
  --window-size=1,1 \
  --no-first-run \
  --disable-popup-blocking \
  --hide-crash-restore-bubble \
  --disable-infobars \
  --no-default-browser-check
```

> ⚠️ **端口 9223**：与头条项目（9222）隔离，可同时运行。

### 首次登录

```bash
python main.py --login --tenant douyin_music_default
```

使用 **手机验证码登录**（推荐）：
1. 浏览器弹出登录窗口
2. 切换到「验证码登录」tab
3. 输入手机号 → 获取验证码
4. 在终端中输入收到的验证码
5. Session 自动持久化，下次启动无需重复登录

> Session 有效期约 5-10 分钟，过期需重新登录。

---

## CLI 使用

```bash
# 查看租户列表
python main.py --list-tenants

# 登录（验证码方式）
python main.py --login --tenant douyin_music_default

# 完整工作流（热搜分析 → 创意 → 词曲 → 发布）
python main.py --full --tenant douyin_music_default
```

---

## 单曲导出

从「作曲页」AI 作品导出到「我的资产」页的独立脚本。

```bash
cd ~/.hermes/auto-douyinmusic
source .venv/bin/activate

# 前提：Chrome 9223 已启动且已登录
python export_v5.py "<歌曲名>"
```

### 7 步导出流程

```
作曲页 (/studio/create)
  Step 1 → 点击素材列表中的歌曲
  Step 2 → 点击「AI 编辑」按钮
  Step 3 → 点击「去 AI 编辑器」按钮
  Step 4 → 进入编辑器，等歌曲加载完成
  Step 5 → 点击「导出」按钮（semi-button）
  Step 6 → 修改歌名 → 确认导出
  Step 7 → 验证资产页出现歌曲名
```

### 关键选择器

| 步骤 | 选择器 |
|------|--------|
| 素材列表 | `//div[contains(@class,"libraryItemWrapper") and contains(.,"歌名")]` |
| AI 编辑 | `button[class*="aiEditButton"]` |
| 去 AI 编辑器 | `button[class*="primaryBtn"]` |
| 导出按钮 | `button.semi-button-secondary` |
| 确认导出 | `button.semi-button-primary` |

### 信号处理

`export_v5.py` 内置 SIGTERM/SIGINT 信号处理，被杀时自动清理 Chrome 9223 进程：

```python
def _cleanup(signum, frame):
    os.system("lsof -ti :9223 | xargs kill -9 2>/dev/null")
    os._exit(0)
```

---

## 项目结构

```
.
├── main.py                       # CLI 入口
├── config.yaml                   # 全局配置 + 租户定义
├── requirements.txt              # Python 依赖
│
├── infrastructure/               # 基础设施层
│   ├── browser.py                # BrowserCore — DrissionPage 封装
│   ├── llm_client.py             # LLMClient — DeepSeek API 调用
│   └── platform/                 # 平台适配（预留）
│
├── models/                       # 数据模型
│   ├── config.py                 # 配置加载（YAML + .env）
│   └── song.py                   # 歌曲相关数据模型
│
├── pipelines/                    # Pipeline 定义
│   ├── base.py                   # BasePipeline 抽象类
│   └── music_creation.py         # 音乐创作 Pipeline
│
├── services/                     # 业务逻辑层
│   ├── agents/                   # Agent 层
│   │   ├── base.py               # BaseAgent
│   │   ├── orchestrator.py       # 主控 Agent（V4 Pro）
│   │   ├── collector_analyst.py  # 热搜分析 Agent
│   │   ├── creative_director.py  # 创意总监 Agent
│   │   ├── songwriter.py         # 词曲创作 Agent
│   │   └── publisher.py          # 发布 Agent
│   ├── collector_service.py      # 热搜采集服务
│   ├── composition_service.py    # 作曲服务（浏览器操作）
│   ├── lyrics_service.py         # 歌词生成服务（LLM）
│   ├── editor_service.py         # 编辑器操作服务
│   └── publish_service.py        # 发布服务
│
├── presentation/                 # 展示层（预留）
│
├── export_v5.py                  # 单曲导出脚本（稳定版）
├── check_assets.py               # 资产页验证脚本
│
├── start_chrome.sh               # 启动 Chrome（隐藏窗口，推荐）
├── start_chrome_hidden.sh        # 同上（旧版）
├── start_headless_chrome.sh      # 纯无头模式（不推荐，WebSocket 兼容性差）
│
└── 项目记忆.md                    # 完整踩坑记录（开发参考）
```

---

## Agent 架构详解

### OrchestratorAgent（主控）

- **模型**: `deepseek-v4-pro`（更强推理，更高成本）
- **角色**: AI 音乐制作人
- **职责**: 
  - 统筹工作流：数据收集 → 创意策划 → 词曲创作 → 制作发行
  - 质量门禁：每个节点检查输出，不达标则要求返工
  - 数据驱动决策，不凭感觉

### 子 Agent（全部使用 `deepseek-chat`）

| Agent | 职责 | 输出 |
|-------|------|------|
| **CollectorAnalyst** | 分析热搜，识别热门风格 | 市场趋势报告 |
| **CreativeDirector** | 生成歌曲设计方案 | 歌曲蓝图（JSON） |
| **Songwriter** | 生成歌词和作曲提示 | 结构化歌词 + 风格描述 |
| **Publisher** | 发布全曲、管理签约 | 发行结果 |

### 双模型策略

```
主控 Agent: deepseek-v4-pro  ← 高质量推理，把控全局
     └── 子 Agent: deepseek-chat  ← 性价比高，处理具体任务
```

子 Agent 复用主控的 llm client 配置，降低 token 消耗。

---

## 已知问题 & 踩坑记录

详见 [`项目记忆.md`](./项目记忆.md) 完整记录。以下仅列关键坑点：

### 🔥 1. `--headless=new` WebSocket 404

DrissionPage 4.1.x 不兼容 Chrome 147+ 的 `--headless=new` 模式。  
**解法**：用窗口隐藏模式替代：`--window-position=-32000,-32000 --window-size=1,1`

### 🔥 2. DrissionPage 静默启动 Chrome 到临时目录

当 9223 端口无 Chrome 时，`ChromiumPage(addr_or_opts='127.0.0.1:9223')` 会**静默**启动 Chrome 到临时目录，导致之前登录的 Session 全部丢失。  
**解法**：先手动启动 Chrome（指定 `--user-data-dir`），等 2-3 秒后再连接。

### 🔥 3. 点击导出按钮无响应

Semi UI 的按钮结构是 `<button> → <span>导出</span>`，需要点 `<button>` 本身。  
**解法**：用 `mousedown+mouseup+click` 三重事件链触发。

### 🔥 4. 歌名变成 `[object HTMLInputElement]`

导出弹窗中 input 默认是 `disabled` 状态，直接改值会出异常。  
**解法**：先 `inp.disabled = false; inp.removeAttribute('disabled')`，再用 nativeSetter 改值。

### 🔥 5. 脚本被杀后 Chrome 残留

**解法**：注册信号处理器，收到 SIGTERM 时主动 `lsof -ti :9223 | xargs kill -9`

---

## 开发指南

### 添加新 Agent

```python
# services/agents/your_agent.py
from services.agents.base import BaseAgent

YOUR_PROMPT = """..."""

class YourAgent(BaseAgent):
    async def run(self, context: dict) -> dict:
        # 实现你的业务逻辑
        pass
```

在 `OrchestratorAgent` 中注册即可。

### 添加新 Pipeline

```python
# pipelines/your_pipeline.py
from pipelines import register
from pipelines.base import BasePipeline

@register("your_pipeline")
class YourPipeline(BasePipeline):
    def __init__(self, tenant):
        super().__init__(tenant)
        # 初始化浏览器、LLM 等
```

### 浏览器操作注意事项

- 使用 `BrowserCore` 连接已有 Chrome 实例，不要自动创建
- SPA 页面操作前先确认元素存在
- 修改 React 组件的 input 值时用 nativeSetter（`Object.getOwnPropertyDescriptor`）
- 操作间加适当的等待（1-3 秒），不要用固定 sleep

---

## 许可证

MIT
