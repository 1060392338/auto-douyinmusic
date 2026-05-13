"""在头条找AI用户并关注"""
import time, json, requests, websocket
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 搜索AI
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/search/?keyword=AI';")
time.sleep(6)

# 点击"用户"tab
print("点击用户tab...", flush=True)
P.run_js("""
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '用户') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
""")
time.sleep(5)

text = P.ele('tag:body', timeout=5).text
print(f"用户页文本长度: {len(text)}", flush=True)
print(text[:1000], flush=True)

# 检查关注按钮
if '关注' in text:
    print("\n✅ 有关注按钮！开始关注...", flush=True)
    
    followed = 0
    for scroll_pos in [0, 300, 600, 900, 1200, 1500]:
        P.run_js(f"window.scrollTo(0, {scroll_pos});")
        time.sleep(2)
        
        # 点击未关注的"关注"按钮
        P.run_js("""
        document.querySelectorAll('*').forEach(function(el) {
            var t = (el.textContent || '').trim();
            if (t === '关注' && el.offsetParent !== null) {
                // 确保不是"已关注"按钮
                if (el.className.indexOf('followed') < 0 && el.className.indexOf('active') < 0) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                }
            }
        });
        """)
        time.sleep(2)
        
        new_text = P.ele('tag:body', timeout=5).text
        new_followed = new_text.count('已关注')
        if new_followed > followed:
            diff = new_followed - followed
            followed = new_followed
            print(f"  关注了 {diff} 个, 累计 {followed} 个", flush=True)
        
        if followed >= 10:
            print("  已关注10个，够了", flush=True)
            break
    
    print(f"\n✅ 共关注 {followed} 个AI账号", flush=True)
else:
    print("❌ 没有关注按钮", flush=True)
    print(f"文本中'关注'出现次数: {text.count('关注')}", flush=True)
    
    # 看看页面有什么按钮
    btns = P.eles('tag:button')
    for b in btns:
        t = b.text.strip()
        if t:
            print(f"  按钮: '{t}'", flush=True)

print("\n✅ 完成", flush=True)
