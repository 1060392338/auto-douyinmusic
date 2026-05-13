"""从文章页关注作者"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 去我们刚发布的文章 - 找附近相关AI账号
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/article/7638201530453148201/';")
time.sleep(8)

text = P.ele('tag:body', timeout=5).text
print(f"文章页: {len(text)}字", flush=True)

# 找关注按钮
if '关注' in text:
    # 点击关注按钮 - 排除导航栏和已关注的
    P.run_js("""
    document.querySelectorAll('span, div, p, button').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '关注' && el.offsetParent !== null) {
            // 检查是否是导航栏元素
            var rect = el.getBoundingClientRect();
            if (rect.y > 100) {  // 排除顶部导航栏（通常在前100px）
                // 检查附近没有已关注
                var parent = el.parentElement;
                var skip = false;
                while (parent && parent != document.body) {
                    if (parent.textContent.indexOf('已关注') >= 0) {
                        skip = true; break;
                    }
                    parent = parent.parentElement;
                }
                if (!skip) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                }
            }
        }
    });
    """)
    time.sleep(3)
    
    text2 = P.ele('tag:body', timeout=5).text
    followed = text2.count('已关注')
    print(f"✅ 已关注统计: {followed} 个", flush=True)
else:
    print("❌ 无关注按钮", flush=True)

# 再滚动找更多推荐AI账号
print("\n滚动加载更多...", flush=True)
for sp in [300, 600, 900, 1200, 1500, 2000]:
    P.run_js(f"window.scrollTo(0, {sp});")
    time.sleep(2)
    
    P.run_js("""
    document.querySelectorAll('span, div, p').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '关注' && el.offsetParent !== null) {
            var rect = el.getBoundingClientRect();
            if (rect.y > 100) {
                var parent = el.parentElement;
                var skip = false;
                while (parent && parent != document.body) {
                    if (parent.textContent.indexOf('已关注') >= 0) {
                        skip = true; break;
                    }
                    parent = parent.parentElement;
                }
                if (!skip) {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.focus();
                    el.click();
                }
            }
        }
    });
    """)
    time.sleep(2)

text3 = P.ele('tag:body', timeout=5).text
followed = text3.count('已关注')
print(f"\n✅ 最终已关注: {followed} 个", flush=True)

print("\n✅ 完成", flush=True)
