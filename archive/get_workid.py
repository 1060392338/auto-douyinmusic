#!/usr/bin/env python3
"""提取蝉声漫旧夏的work-id并导航到发布页"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
print("URL:", P.url)
time.sleep(2)

# 提取卡片data-work-id
result = P.run_js("""
(function() {
    var cards = document.querySelectorAll("[class*='assetItemWrapper']");
    var results = [];
    for (var i = 0; i < cards.length; i++) {
        var title = cards[i].getAttribute('data-title') || '';
        var workId = cards[i].getAttribute('data-work-id') || '';
        if (title.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f') >= 0) {
            return JSON.stringify({title: title, workId: workId});
        }
    }
    return 'not found';
})();
""")
print("卡片数据:", result)

# 如果找到了workId，直接导航到发布页
if result and result != 'not found' and result != 'None':
    import json
    try:
        data = json.loads(result)
        work_id = data.get('workId', '')
        if work_id:
            url = f"https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId={work_id}"
            print("导航到:", url)
            P.run_js(f"window.location.href='{url}';")
            time.sleep(6)
            print("新URL:", P.url)
    except:
        print("JSON解析失败:", result)
