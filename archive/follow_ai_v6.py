"""从搜索结果找用户主页链接并关注"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

P.run_js("window.onbeforeunload=null;window.location.href='https://so.toutiao.com/search/?keyword=AI&dvpf=pc&type=user&pd=synthesis&source=search_subtab_switch';")
time.sleep(8)

# 找所有用户相关的链接
links = P.eles('tag:a')
user_links = []
for a in links:
    href = a.attr('href') or ''
    text = (a.text or '').strip()
    # 头条用户主页链接格式
    if '/c/user/' in href and text and len(text) <= 20:
        user_links.append((text, href))
        print(f"  用户: '{text}' -> {href[:80]}", flush=True)

print(f"\n找到 {len(user_links)} 个用户链接", flush=True)

# 访问前5个用户主页并关注
followed = 0
for name, url in user_links[:5]:
    print(f"\n=== 访问 {name} ===", flush=True)
    
    # 确保有完整URL
    if not url.startswith('http'):
        url = 'https://www.toutiao.com' + url
    
    P.run_js(f"window.onbeforeunload=null;window.location.href='{url}';")
    time.sleep(6)
    
    text = P.ele('tag:body', timeout=5).text
    print(f"  主页文本: {text[:400]}", flush=True)
    
    # 关注
    if '关注' in text:
        P.run_js("""
        document.querySelectorAll('span, div, button, p').forEach(function(el) {
            var t = (el.textContent || '').trim();
            if (t === '关注' && el.offsetParent !== null) {
                var parent = el.parentElement;
                var isFollowed = false;
                while (parent) {
                    if (parent.textContent.indexOf('已关注') >= 0) {
                        isFollowed = true; break;
                    }
                    parent = parent.parentElement;
                }
                if (!isFollowed) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                }
            }
        });
        """)
        time.sleep(3)
        
        text2 = P.ele('tag:body', timeout=5).text
        if '已关注' in text2:
            followed += 1
            print(f"  ✅ 已关注 {name} (累计{followed})", flush=True)
        else:
            print(f"  ❌ 关注可能失败", flush=True)
    else:
        print(f"  ❌ 无关注按钮", flush=True)
    
    time.sleep(2)

print(f"\n✅ 共关注 {followed} 个AI账号", flush=True)
