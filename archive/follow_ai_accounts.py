"""在头条关注同类型AI账号"""
import time, json, requests, websocket
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 导航到头条搜索AI相关
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/search/?keyword=AI';")
time.sleep(6)

body = P.ele('tag:body', timeout=5)
text = body.text
print(f"搜索页文本长度: {len(text)}", flush=True)
print(text[:500], flush=True)

# 找关注按钮
btns = P.eles('tag:button')
focus_btns = [(b.text.strip(), b.outer_html[:100]) for b in btns if b.text.strip() and len(b.text.strip()) < 10]
print(f"\n按钮列表:", flush=True)
for t, html in focus_btns:
    print(f"  '{t}' -> {html}", flush=True)

# 检查是否有"关注"按钮
if '关注' in text:
    print("\n✅ 有关注按钮！", flush=True)
    
    # 翻看搜索结果
    for scroll_pos in [0, 500, 1000, 1500, 2000]:
        P.run_js(f"window.scrollTo(0, {scroll_pos});")
        time.sleep(2)
        
        # 点击关注
        P.run_js("""
        document.querySelectorAll('*').forEach(function(el) {
            var t = (el.textContent || '').trim();
            if (t === '关注' && el.offsetParent !== null) {
                // 检查是否已被关注
                var parent = el.parentElement;
                var isFollowed = false;
                while (parent) {
                    if (parent.textContent.indexOf('已关注') >= 0) {
                        isFollowed = true;
                        break;
                    }
                    parent = parent.parentElement;
                }
                if (!isFollowed) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                    console.log('已关注一个账号');
                }
            }
        });
        """)
        time.sleep(1)
    
    print("\n关注操作完成", flush=True)
    
    # 查看到底关注了几个
    text2 = P.ele('tag:body', timeout=5).text
    focus_count = text2.count('已关注')
    print(f"检测到 {focus_count} 个已关注状态", flush=True)
else:
    print("❌ 未找到关注按钮", flush=True)

print("\n✅ 完成", flush=True)
