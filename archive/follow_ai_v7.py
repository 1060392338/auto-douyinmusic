"""从AI文章找作者关注"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 去头条科技频道找AI文章
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/ch/technology/';")
time.sleep(8)

text = P.ele('tag:body', timeout=5).text
print(f"科技频道: {len(text)}字", flush=True)
print(text[:500], flush=True)

# 找关注按钮
if '关注' in text:
    print("\n✅ 有关注按钮！", flush=True)
    
    followed = 0
    for scroll_pos in range(0, 2000, 400):
        P.run_js(f"window.scrollTo(0, {scroll_pos});")
        time.sleep(2)
        
        # 点击"关注"按钮（确保不是已关注的）
        P.run_js("""
        document.querySelectorAll('*').forEach(function(el) {
            var t = (el.textContent || '').trim();
            if (t === '关注' && el.offsetParent !== null) {
                // 检查附近没有"已关注"
                var parent = el.parentElement;
                var skip = false;
                for (var p = parent; p; p = p.parentElement) {
                    if (p.textContent.indexOf('已关注') >= 0) {
                        skip = true; break;
                    }
                }
                if (!skip) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                }
            }
        });
        """)
        time.sleep(2)
    
    # 统计
    text2 = P.ele('tag:body', timeout=5).text
    followed = text2.count('已关注')
    print(f"\n✅ 检测到 {followed} 个已关注", flush=True)
else:
    print("❌ 没有关注按钮", flush=True)
    
    # 看按钮
    btns = P.eles('tag:button')
    for b in btns:
        t = b.text.strip()
        if t:
            print(f"  按钮: '{t}'", flush=True)

print("\n✅ 完成", flush=True)
