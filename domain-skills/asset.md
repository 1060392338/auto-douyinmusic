# 资产管理操作手册

> 页面：`https://music.douyin.com/studio/assets`

---

## 页面结构

资产页以 `[class*="assetItemWrapper"]` 列表展示所有作品。每个项目包含：
- `data-title` 属性：歌名
- `assetDuration`：时长
- `assetTimestamp`：时间戳
- 文本中包含"发行全曲" → 可发布

## 检查脚本

```bash
python scripts/check_assets.py
```

输出格式：
```
资产页共 15 首作品：
  1. 纸鸢远    4:20 10:30 🔴 可发行
  2. 夏蝉语    3:45 11:15 🔴 可发行
  ...
```

## 操作

| 操作 | 命令 | 说明 |
|------|------|------|
| 检查已导出 | `python scripts/check_assets.py` | 列出所有作品和发布状态 |
| 删除单曲 | 需人工操作（浏览器中点... → 删除） | |
| 批量删除 | `python scripts/batch_delete.py` | 慎用 |
