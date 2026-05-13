"""从个人主页找推荐关注的作者"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 去个人主页
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/c/user/token/MS4wLjABAAAAdN3ILbI_NdxHSQruwLOJcm78tRCRCIf';")
time.sleep(6)

text = P.ele('tag:body', timeout=5).text
print(f"个人主页: {len(text)}字", flush=True)

# 找"关注"、"推荐作者"、"你可能感兴趣"等推荐关注的词
for kw in ['推荐作者', '你可能感兴趣', '大家都在看', '推荐关注', '发现更多']:
    if kw in text:
        print(f"✅ {kw}", flush=True)

# 找所有可见的"关注"按钮——不是导航栏里的
# 用DrissionPage的eles方法查找
for el in P.eles('xpath://*[text()="关注"]'):
    try:
        t = el.text.strip()
        rect_info = P.run_js(f"var r = arguments[0].getBoundingClientRect(); return JSON.stringify({{y: r.y, w: r.width, h: r.height}});", el)
        print(f"  关注元素: tag={el.tag} text='{t}' rect={rect_info}", flush=True)
    except:
        pass

# 也找div/span文本
all_els = P.eles('xpath://*[self::span or self::div or self::p or self::button][text()="关注"]')
print(f"\n共找到 {len(all_els)} 个'关注'元素", flush=True)

# 找不到就看看有啥按钮
btns = P.eles('tag:button')
for b in btns:
    t = b.text.strip()
    if t and len(t) < 10:
        print(f"  按钮: '{t}'", flush=True)

print("\n✅ 完成", flush=True)
