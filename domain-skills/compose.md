# AI作曲页操作手册

> 页面：`https://music.douyin.com/studio/create`
> 端口：9223 | 连接：`ChromiumPage(addr_or_opts='127.0.0.1:9223')`

---

## 页面结构

```
AI作曲 页面
├── 灵感模式（默认） → 单 textarea 输入
├── 高级模式 → 点击「高级模式」按钮切换
│   ├── 输入框1：曲风/风格描述 ↕
│   └── 输入框2：歌词（可空白）
└── 提交按钮（semi-chat-inputBox-sendButton）
```

## 关键选择器

| 元素 | 选择器 | 说明 |
|------|--------|------|
| AI作曲导航 | `div.navigation-item-wrapper-LJh_pw` | 文本="AI 作曲"（注意有空格） |
| 灵感模式输入框 | `textarea.semi-input-textarea` | placeholder="描述你的音乐灵感..." |
| 高级模式按钮 | 文本="高级模式" | 需要先点击切换到高级 |
| 高级-风格输入 | `div.semi-input-wrapper textarea` | 多 textarea 中的第一个 |
| 高级-歌词输入 | `div.semi-input-wrapper textarea` | 多 textarea 中的第二个 |
| 提交按钮 | `button.semi-chat-inputBox-sendButton` | 需要先输入内容才会 enabled |

## 操作步骤

### 灵感模式（推荐调试用）
1. 导航到 `/studio/create`
2. 选择「AI作曲」导航项（若不在该页）
3. 等 3s 确保页面渲染完成
4. 在 textarea 中填写 prompt
5. 等按钮 enabled → 点击提交

### 高级模式（推荐生产用）
1. 导航到 `/studio/create`
2. 选择「AI作曲」导航项
3. 点击「高级模式」切换按钮
4. 风格输入框：填写曲风（如 Pop, Rock, EDM）
5. 歌词输入框：可选，填写歌词片段
6. 等提交按钮 enabled → 点击提交

## React 输入坑

**必须用原生 InputEvent，普通 value= 无效**：
```javascript
// ✅ 正确的 React 输入方式
const input = document.querySelector('textarea');
let nativeSetter = Object.getOwnPropertyDescriptor(
  window.HTMLTextAreaElement.prototype, 'value'
).set;
nativeSetter.call(input, '我的prompt');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));
```

## 生成状态检测

- 生成中：页面出现灰色卡片，状态文本不含"生成中"
- 生成完成：灰色卡片变为彩色，可点击操作
- 生成失败：按钮重新 enabled，无新卡片出现
- 超时策略：等 120s → 去资产页检查（可能成功了但 UI 没刷新）

## 已知失败模式

| 失败模式 | 现象 | 处理 |
|----------|------|------|
| 服务端拒绝 | 按钮变灰 → API 返回"生成失败" | 换 prompt 重试 ≤3 次 |
| 按钮不可点击 | `disabled=true` | 检查是否已正确输入（React state 未更新） |
| 超时无结果 | 120s 无灰色卡片 | 跳资产页确认；再重试 1 次 |
