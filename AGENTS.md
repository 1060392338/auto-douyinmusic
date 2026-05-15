# 抖音音乐开放平台自动化 · AGENTS.md

> **仓库即记录系统** — 所有知识在此，不在 Agent 的记忆里。
> 最后更新：2026-05-14 | Harness Engineering✅

---

## 一、三秒速览

| 做什么 | 命令 |
|--------|------|
| 启动 Chrome | `bash scripts/start.sh` |
| 作曲 | `python main.py --compose --prompt "..."` |
| 导出单曲 | `python export_v5.py <歌名>` |
| 检查资产 | `python scripts/check_assets.py` |
| 登录 | `python scripts/login.py` |

---

## 二、仓库地图

```
auto-douyinmusic/
├── AGENTS.md              ← 🏠 你在这里
├── ARCHITECTURE.md        ← 架构约束（AI 不可违背）
├── domain-skills/         ← 📖 页面操作手册（每条一问）
│   ├── compose.md         — AI作曲页操作
│   ├── export.md          — 导出到资产页流程
│   ├── login.md           — 登录流程
│   ├── asset.md           — 资产管理
│   └── publish.md         — 发布流程（人工操作）
├── selectors/             ← 🎯 已验证选择器映射
│   ├── index.md           — 全局选择器索引
│   └── data-testid/       — 原始 data-testid 快照
├── scripts/               ← ⚙️ 机械化检查 & 工具脚本
│   ├── page_check.py      — 运行前页面状态断言
│   └── check_assets.py    — 资产页检查
├── infrastructure/        ← 浏览器/CDP/LLM 基础设施
├── services/              ← 业务服务（Agent可调用）
├── pipelines/             ← Pipeline 编排
├── models/                ← 数据模型
├── export_v5.py           ← 🔑 单曲导出（生产级）
├── export_cdp.py          ← 🧪 CDP导出备用
└── main.py                ← CLI入口
```

---

## 三、核心约束（机械执行）

运行任何脚本 **前**：`python scripts/page_check.py`
- 失败 → 不要往下走，先修前提条件

### 选择器规则
1. **优先 `data-testid`**（如 `[data-testid="composeSubmitBtn"]`）
2. 其次 `button[class*="xxx"]`（固定前缀匹配）
3. **永不**只用 `.class-name`（hash后缀每版本变）
4. 见 `selectors/index.md` 完整映射

### 错误分类
| 类型 | 表现 | 动作 |
|------|------|------|
| form_invalid | 按钮 disabled / 输入框无反应 | 重填，检查 selectors |
| api_rejected | 按钮变灰，显示错误提示 | 换 prompt 重试 ≤3 次 |
| api_timeout | 等待 120s 无结果 | 去资产页检查（可能成功） |
| session_expired | 跳回登录页 | 通知用户重新扫码 |

### 熵管理
- **临时脚本用完速删**，不进仓库
- 每会话结束清理：`compose_*.py`, `test_*.py`, `debug_*.py`
- archive/ 已永久删除（110 个版本碎片，不再重建）

---

## 四、快速参考

### Chrome 配置
```bash
端口: 9223
user-data-dir: ~/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data
模式: 窗口隐藏（--window-position=-32000,-32000）
```

### 按键顺序
```
compose:  Chrome 9223 → 导航/studio/create → 填prompt → 等生成 → 导出
login:    Chrome 9223 → 导航/studio/create → 验证码登录
export:   Chrome 9223 → export_v5.py <歌名>
check:    Chrome 9223 → check_assets.py
```

---

## 五、相关链接
- `skill: douyin-music-studio` — 完整的 4Agent 架构文档
- `github.com/deusyu/harness-engineering` — 本仓库遵循的工程范式
- `~/.hermes/senlan-automation/AGENTS.md` — 森蓝ERP项目同样结构
