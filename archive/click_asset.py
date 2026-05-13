#!/usr/bin/env python3
"""点击蝉声漫旧夏卡片进入详情页"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

# 清除弹窗
for _ in range(3):
    try:
        P.handle_alert(accept=True)
        time.sleep(0.5)
    except:
        break

# 点击资产卡片
P.run_js("""
(function() {
    var items = document.querySelectorAll("[class*='assetItemWrapper']");
    for (var i = 0; i < items.length; i++) {
        if (items[i].textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f') >= 0) {
            items[i].scrollIntoView({behavior:'instant', block:'center'});
            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                items[i].dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
            });
            return;
        }
    }
})();
""")
time.sleep(5)
print("URL:", P.url)

# 用JS获取body文本
js = """
(function() {
    var b = document.body;
    return b ? b.innerText.substring(0, 600) : 'no body';
})();
"""
body_text = P.run_js(js)
print("body:", body_text)

# 找发行全曲按钮
js2 = """
(function() {
    var all = document.querySelectorAll("*");
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent && all[i].textContent.trim() === "\u53d1\u884c\u5168\u66f2") {
            return all[i].tagName + " " + (all[i].className || "").substring(0, 60);
        }
    }
    return "not found";
})();
"""
result = P.run_js(js2)
print("发行全曲元素:", result)
