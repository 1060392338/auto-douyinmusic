#!/usr/bin/env python3
"""从资产页点击发行全曲进入预填发布表单"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 先清除可能存在的弹窗
for _ in range(3):
    try:
        P.handle_alert(accept=True)
        time.sleep(0.5)
    except:
        break

# 导航到资产页
P.run_js("window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(5)
print("1. 已在资产页:", P.url[:60])

# 找到蝉声漫旧夏卡片上的"发行全曲"文字并点击
# 发行全曲可能是一个div/span/button，在卡片内部
P.run_js("""
(function() {
    // 找所有包含"发行全曲"的元素
    var all = document.querySelectorAll("*");
    for (var i = 0; i < all.length; i++) {
        var t = all[i].textContent;
        if (t && t.trim() === "\u53d1\u884c\u5168\u66f2") {
            // 检查这个元素是否在蝉声漫旧夏卡片内
            var parent = all[i].parentElement;
            var found = false;
            for (var p = parent; p; p = p.parentElement) {
                if (p.textContent && p.textContent.indexOf("\u8749\u58f0\u6f2b\u65e7\u590f") >= 0) {
                    found = true;
                    break;
                }
            }
            if (found || parent.textContent.indexOf("\u8749\u58f0\u6f2b\u65e7\u590f") >= 0) {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                setTimeout(function() {
                    all[i].click();
                }, 200);
                return "clicked";
            }
        }
    }
    return "not found";
})();
""")
time.sleep(5)
print("2. 点击后URL:", P.url[:80])

# 查看页面内容
text = P.run_js("document.body.innerText.substring(0,600)")
print("3. 页面内容:", text)
