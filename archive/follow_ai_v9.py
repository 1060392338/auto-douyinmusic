"""搜索并关注知名AI账号"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 尝试直接访问已知AI账号主页（通过头条的搜索跳转机制）
# 头条的搜索会跳转到用户主页
account_pages = {
    "量子位": "https://www.toutiao.com/c/user/6776074100526080519/",
    "AI科技评论": "https://www.toutiao.com/c/user/51336505642/",
    "机器之心": "https://www.toutiao.com/c/user/50502213389/",
}

for name, url in account_pages.items():
    print(f"\n=== 访问 {name} ===", flush=True)
    P.run_js(f"window.onbeforeunload=null;window.location.href='{url}';")
    time.sleep(6)
    
    text = P.ele('tag:body', timeout=5).text
    print(f"  文本: {text[:300]}", flush=True)
    
    # 找"关注"按钮 - 在作者主页上仔细找
    # 查找包含"关注"且不是"已关注"或tab的元素
    P.run_js("""
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '关注' && el.offsetParent !== null) {
            // 排除导航栏（top < 50px的）
            var rect = el.getBoundingClientRect();
            if (rect.bottom > 60) {
                // 检查父元素是否有"已关注"
                var parent = el.parentElement;
                var isFollowed = false;
                for (var p = parent; p && p != document.body; p = p.parentElement) {
                    if (p.textContent.indexOf('已关注') >= 0) {
                        isFollowed = true; break;
                    }
                }
                if (!isFollowed) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                    console.log('关注了:', t);
                }
            }
        }
    });
    """)
    time.sleep(3)
    
    text2 = P.ele('tag:body', timeout=5).text
    if '已关注' in text2:
        print(f"  ✅ 已关注 {name}!", flush=True)
    else:
        print(f"  ❌ 关注失败", flush=True)
    
    time.sleep(2)

print("\n✅ 完成", flush=True)
