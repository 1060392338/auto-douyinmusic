"""检查蝉声漫旧夏是否发布成功"""
import time, sys
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 用 JS 直接导航到资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/asset/music';")
time.sleep(6)

print(f"当前URL: {P.url}", flush=True)
print(f"页面标题: {P.title}", flush=True)

body = P.ele('tag:body')
text = body.text
print(f"页面文本长度: {len(text)}", flush=True)

# 检查是否未登录
if '登录' in text and ('扫码登录' in text or '请输入手机号' in text):
    print("❌ 未登录 - 需要先登录", flush=True)
    sys.exit(1)

# 查找蝉声漫旧夏
if '蝉声漫旧夏' in text:
    print("✅ 找到「蝉声漫旧夏」", flush=True)
    # 找到包含蝉声漫旧夏的上下文本
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if '蝉声漫旧夏' in line:
            start = max(0, i-3)
            end = min(len(lines), i+4)
            print(f"\n--- 上下文 (行{i}) ---", flush=True)
            for j in range(start, end):
                marker = ">" if j == i else " "
                print(f"{marker} {lines[j].strip()}", flush=True)
            print("---", flush=True)
else:
    print(f"❌ 未找到「蝉声漫旧夏」", flush=True)
    # 列出所有可能的歌曲名
    lines = text.split('\n')
    songs = [l.strip() for l in lines if 2 <= len(l.strip()) <= 8 and not l.strip().startswith(('0','1','2','3','4','5','6','7','8','9','/','\\','<'))]
    if songs:
        print(f"找到的可能歌曲名: {songs[:20]}", flush=True)

# 检查发行全曲/已发布/审核等关键词
for kw in ['发行全曲', '已发布', '审核中', '审核通过', '发行成功', '已发行', '处理中', '发布失败']:
    if kw in text:
        print(f"✅ 找到关键词: {kw}", flush=True)

print("\n✅ 检查完成", flush=True)
