import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 清除弹窗
for _ in range(5):
    try:
        P.handle_alert(accept=True)
        print("alert cleared")
        time.sleep(0.5)
    except:
        break

# 导航到资产页 - 用run_js避免beforeunload
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(5)
print("URL:", P.url[:60])

# 找蝉声漫旧夏卡片上的"发行全曲"
P.run_js("""
(function() {
    window.onbeforeunload = null;
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent && all[i].textContent.trim() === '\u53d1\u884c\u5168\u66f2') {
            // 检查是否在蝉声漫旧夏卡片内
            for (var p = all[i]; p; p = p.parentElement) {
                if (p.textContent && p.textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f') >= 0) {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    setTimeout(function() {
                        all[i].click();
                    }, 300);
                    return;
                }
            }
        }
    }
})();
""")
time.sleep(5)
print("POST_CLICK:", P.url[:80])

# 看看页面
txt = P.run_js("document.body.innerText.substring(0,400)")
print("BODY:", txt)
