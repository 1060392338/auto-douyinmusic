"""更健壮的AI账号关注"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/search/?keyword=AI&type=user';")
time.sleep(8)

# 获取所有可点击元素
all_links = P.eles('tag:a')
print(f"链接数: {len(all_links)}", flush=True)
for a in all_links[:10]:
    t = (a.text or '').strip()
    if t and len(t) > 1:
        href = a.attr('href') or ''
        print(f"  '{t}' href={href[:80]}", flush=True)

# 点击用户头像/卡片
print("\n点击用户卡片...", flush=True)
P.run_js("""
document.querySelectorAll('a, div[class*="card"], div[class*="user"]').forEach(function(el) {
    var t = (el.textContent || '').trim();
    // 找到AI相关用户
    if (el.offsetParent !== null && 
        (t.indexOf('AI') >= 0 || t.indexOf('人工智能') >= 0) &&
        t.indexOf('万粉丝') >= 0 && el.children.length > 0) {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        el.click();
        return;
    }
});
""")
time.sleep(5)

print(f"当前URL: {P.url[:80]}", flush=True)
text = P.ele('tag:body', timeout=5).text
print(f"文本前300: {text[:300]}", flush=True)

# 找关注按钮
if '关注' in text:
    print("✅ 有关注按钮!", flush=True)
    P.run_js("""
    document.querySelectorAll('span, div, button').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '关注' && el.offsetParent !== null) {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus();
            el.click();
        }
    });
    """)
    time.sleep(3)
    text2 = P.ele('tag:body', timeout=5).text
    if '已关注' in text2:
        print("✅ 已成功关注!", flush=True)
else:
    print("❌ 未找到关注按钮", flush=True)

print("\n✅ 完成", flush=True)
