"""从 studio 内导航到资产页"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 先去 studio
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(6)

body = P.ele('tag:body').text
print(f"Studio 页 text length: {len(body)}", flush=True)
print(f"Studio 内容前500字:", flush=True)
print(body[:500], flush=True)

# 找所有导航项
navs = P.eles('xpath://div[contains(@class,"navigation-item-wrapper")]')
print(f"\n导航项数量: {len(navs)}", flush=True)
for n in navs:
    print(f"  导航: {n.text.strip()}", flush=True)

# 尝试找到「我的资产」或类似导航项
for n in navs:
    t = n.text.strip()
    if '资产' in t:
        print(f"\n找到资产导航: {t}", flush=True)
        # 检查是否是 SPA 路由
        print(f"  元素 outer_html: {n.outer_html[:200]}", flush=True)
        
# 直接检查 studio 页上是否有已发布的资产信息
if '蝉声漫旧夏' in body:
    print("\n✅ 蝉声漫旧夏 在 studio 页找到!", flush=True)
    idx = body.find('蝉声漫旧夏')
    print(f"上下文: ...{body[max(0,idx-50):idx+100]}...", flush=True)

# 检查发布相关的文本
for kw in ['发行', '发布', '已发行', '审核']:
    if kw in body:
        print(f"✅ 关键词 {kw} 在 studio 页", flush=True)

# 检查是否可以找到资产相关区域
# 查看是否有提示信息
if 'asset' in body.lower():
    print("✅ 有 asset 相关文本", flush=True)
