# 架构约束（此处为 AI 不可违背的规则）

## 浏览器层

1. **端口 9223** — 与森蓝ERP（9222）隔离，永不冲突
2. **窗口隐藏模式** — `--window-position=-32000,-32000`，不用 `--headless=new`
   - 原因：Chrome 147+ headless 模式下 DrissionPage WebSocket 404
3. **必须先启动 Chrome**，再连接 ChromiumPage
   - 错误：`ChromiumPage(addr_or_opts='127.0.0.1:9223')` 会在 Chrome 未启动时静默创建一个临时目录实例
   - 检查：`ps aux | grep chrome.*9223 | grep -o 'user-data-dir=[^ ]*'`

## 选择器层

1. **优先 data-testid** → `document.querySelector('[data-testid="xxx"]')`
2. **其次 `class*=` 前缀匹配** → `button[class*="aiEditButton"]`
3. **永不直接用 `.className`** — hash 后缀每 QA 版本变
4. 触发 React 事件需用全事件链：`mousedown+mouseup+click`

## 错误处理层

1. 每次 `run_js()` 前处理 alert：`try P.handle_alert(accept=True); except: pass`
2. 导出弹窗 input 是 disabled 的，必须 `disabled=false` 后再 nativeSetter
3. 素材列表渲染需 12s + 滚动 + 4s

## 流程约束

1. **导出单曲，不批量** — shell for 循环 kill 时残留孤儿进程
2. **发布全曲由用户人工操作** — 本系统到资产页为止
3. **session TTL ~5-10 分钟** — 过期需重新验证码登录
