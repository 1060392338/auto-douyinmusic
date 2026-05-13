"""简单检查资产页"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/asset/music';")
time.sleep(10)

body = P.ele('tag:body')
text = body.text
print(f"=== 资产页文本 (len={len(text)}) ===", flush=True)
print(text[:5000], flush=True)
print("\n=== 搜索关键词 ===", flush=True)
for kw in ['蝉声漫旧夏', '发行全曲', '已发布', '已发行', '审核', '新项目']:
    if kw in text:
        # 找到上下文
        idx = text.find(kw)
        start = max(0, idx-50)
        end = min(len(text), idx+100)
        print(f"✅ {kw} -> ...{text[start:end]}...", flush=True)
    else:
        print(f"❌ {kw}", flush=True)
