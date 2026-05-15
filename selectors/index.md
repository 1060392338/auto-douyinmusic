# 全局选择器索引

> 更新策略：每次发现新选择器 → 更新到此 + 对应的 domain-skills/
> 策略：优先 data-testid → `class*=` 前缀 → **永不直接 `.hash-class`**

---

## 导航

| 元素 | 选择器 | 所在文件 |
|------|--------|---------|
| AI作词导航 | `div.navigation-item-wrapper-LJh_pw` (文本="AI 作词") | domain-skills/compose.md |
| AI作曲导航 | `div.navigation-item-wrapper-LJh_pw` (文本="AI 作曲") | domain-skills/compose.md |

## 作曲页（/studio/create）

| 元素 | 选择器 | 备注 |
|------|--------|------|
| 灵感模式输入框 | `textarea.semi-input-textarea` | placeholder="描述你的音乐灵感..." |
| 高级模式风格输入 | 第一个`div.semi-input-wrapper textarea` | |
| 高级模式歌词输入 | 第二个`div.semi-input-wrapper textarea` | |
| 提交按钮 | `button.semi-chat-inputBox-sendButton` | 输入后才 enabled |
| 素材列表项 | `[class*="libraryItemWrapper"]` | 含歌名文本 |
| 素材标题行 | `[class*="titleRow"]` | 对应展开的素材项 |
| AI编辑按钮 | `button[class*="aiEditButton"]` | |
| 去AI编辑器按钮 | `button[class*="primaryBtn"]` | 需 scrollIntoView |

## 编辑器（playground）

| 元素 | 选择器 | 备注 |
|------|--------|------|
| 导出按钮 | `button.semi-button-secondary` | 文本="导出"，需全事件链 |
| 确认导出 | `button.semi-button-primary` | 文本包含"导出"或"并轨导出" |

## 资产页（/studio/assets）

| 元素 | 选择器 | 备注 |
|------|--------|------|
| 作品卡片 | `[class*="assetItemWrapper"]` | data-title=歌名 |
| 时长 | `[class*="assetDuration"]` | |
| 时间戳 | `[class*="assetTimestamp"]` | |

## 登录弹窗

| 元素 | 选择器 |
|------|--------|
| 验证码 tab | 文本="验证码登录" |
| 手机号 | `input[placeholder*="手机号"]` |
| 验证码 | `input[placeholder*="验证码"]` |
