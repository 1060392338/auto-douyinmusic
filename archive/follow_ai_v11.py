"""在头条创作平台找关注功能"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 去创作平台找互动/关注相关页面
P.run_js("window.onbeforeunload=null;window.location.href='https://mp.toutiao.com/profile_v4/graphic/publish';")
time.sleep(6)

text = P.ele('tag:body', timeout=5).text
print(f"创作平台: {len(text)}字", flush=True)

# 找互动/粉丝/关注相关菜单
for kw in ['互动', '粉丝', '关注', '我的关注', '发现', '推荐']:
    if kw in text:
        print(f"✅ 有: {kw}", flush=True)

# 找按钮和链接
links = P.eles('tag:a')
for a in links:
    href = a.attr('href') or ''
    t = (a.text or '').strip()
    if t and len(t) < 20 and ('关注' in t or '互动' in t or '粉丝' in t):
        print(f"  链接: '{t}' -> {href[:80]}", flush=True)

# 找菜单项
navs = P.eles('xpath://div[contains(@class,"menu") or contains(@class,"nav") or contains(@class,"sidebar")]')
for n in navs:
    t = n.text.strip()
    if '关注' in t or '互动' in t or '粉丝' in t:
        print(f"  菜单: {t[:100]}", flush=True)

print("\n✅ 完成", flush=True)
