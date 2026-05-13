#!/usr/bin/env python3
"""点击蝉声漫旧夏卡片 - 无alert处理版"""
import time
from DrissionPage import ChromiumPage

print("connecting...")
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
print("connected, URL:", P.url)
time.sleep(2)

# 点击卡片
print("clicking card...")
P.run_js("""
(function() {
    var items = document.querySelectorAll("[class*='assetItemWrapper']");
    for (var i = 0; i < items.length; i++) {
        if (items[i].textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f') >= 0) {
            items[i].scrollIntoView({behavior:'instant', block:'center'});
            items[i].click();
            return;
        }
    }
})();
""")
print("clicked, waiting...")
time.sleep(5)
print("URL:", P.url)

# 获取页面文本
result = P.run_js("document.body.innerText.substring(0,500)")
print("body:", result)
