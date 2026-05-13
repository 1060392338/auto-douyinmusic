"""点进AI账号主页关注"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9222')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 搜索AI用户
P.run_js("window.onbeforeunload=null;window.location.href='https://www.toutiao.com/search/?keyword=AI&type=user';")
time.sleep(8)

text = P.ele('tag:body', timeout=5).text
print(f"用户搜索页: {len(text)}字", flush=True)

# 提取AI账号名
lines = text.split('\n')
accounts = []
for i, line in enumerate(lines):
    line = line.strip()
    if '粉丝' in line or '万粉丝' in line:
        # 前一行可能是账号名
        for j in range(max(0,i-3), i):
            name = lines[j].strip()
            if name and 2 <= len(name) <= 20 and '粉丝' not in name and '·' not in name:
                accounts.append(name)
                break

print(f"\n找到账号: {accounts[:10]}", flush=True)

# 点击前5个账号进入主页
visited = 0
for name in accounts[:5]:
    print(f"\n访问 {name}...", flush=True)
    P.run_js("""
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '""" + name + """' && el.offsetParent !== null) {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus();
            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
            });
        }
    });
    """)
    time.sleep(5)
    
    text2 = P.ele('tag:body', timeout=5).text
    print(f"  主页文本: {text2[:300]}...", flush=True)
    
    # 找关注按钮
    if '关注' in text2:
        P.run_js("""
        document.querySelectorAll('*').forEach(function(el) {
            var t = (el.textContent || '').trim();
            if (t === '关注' && el.offsetParent !== null) {
                // 不是已关注
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
                    console.log('关注成功');
                }
            }
        });
        """)
        time.sleep(3)
        print(f"  尝试关注", flush=True)
        visited += 1
    else:
        print("  ❌ 无关注按钮", flush=True)
    
    # 返回搜索页
    P.run_js("window.onbeforeunload=null;window.history.back();")
    time.sleep(5)

print(f"\n✅ 访问了 {visited} 个账号主页", flush=True)
print("✅ 完成", flush=True)
