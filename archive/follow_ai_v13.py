"""点击个人主页的关注按钮"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/c/user/token/MS4wLjABAAAAdN3ILbI_NdxHSQruwLOJcm78tRCRCIf';")
time.sleep(6)

# 找到并点击可见的关注按钮(y>50)
# 点击所有非导航栏的关注按钮
P.run_js("""
document.querySelectorAll('div, p, span').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '关注' && el.offsetParent !== null) {
        var rect = el.getBoundingClientRect();
        if (rect.y > 50 && rect.width > 10 && rect.height > 10) {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus();
            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
            });
        }
    }
});
""")
time.sleep(3)

# 检查是否"已关注"
text = P.ele('tag:body', timeout=5).text
followed_count = text.count('已关注')
print(f"已关注数量: {followed_count}", flush=True)

# 滚动加载更多
for sp in [300, 600, 900, 1200]:
    P.run_js(f"window.scrollTo(0, {sp});")
    time.sleep(2)
    P.run_js("""
    document.querySelectorAll('div, p, span').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '关注' && el.offsetParent !== null) {
            var rect = el.getBoundingClientRect();
            if (rect.y > 50 && rect.width > 10 && rect.height > 10) {
                // 检查附近没有"已关注"
                var parent = el.parentElement;
                var isFollowed = false;
                for (var p = parent; p && p !== document.body; p = p.parentElement) {
                    if (p.textContent.indexOf('已关注') >= 0) {
                        isFollowed = true; break;
                    }
                }
                if (!isFollowed) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                        el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
                    });
                }
            }
        }
    });
    """)
    time.sleep(2)
    
    text2 = P.ele('tag:body', timeout=5).text
    fc = text2.count('已关注')
    if fc > followed_count:
        print(f"  累计已关注: {fc}", flush=True)
        followed_count = fc

print(f"\n✅ 共 {followed_count} 个已关注", flush=True)
print("✅ 完成", flush=True)
