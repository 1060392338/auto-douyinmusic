#!/usr/bin/env python3
try:
    import time
    from DrissionPage import ChromiumPage
    P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
    time.sleep(2)
    print("CONNECTED")
    
    # 导航到资产页
    P.run_js("window.location.href='https://music.douyin.com/studio/assets';")
    time.sleep(5)
    print("URL:", P.url[:60])
    
    # 找蝉声漫旧夏卡片里的"发行全曲"并点击
    # 直接用JS操作
    P.run_js("""
    (function() {
        var span = document.evaluate(
            '//*[text()=\"\u53d1\u884c\u5168\u66f2\"]',
            document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
        ).singleNodeValue;
        if (span) {
            span.scrollIntoView();
            span.click();
        }
    })();
    """)
    time.sleep(5)
    print("POST_CLICK_URL:", P.url[:80])
except Exception as e:
    print(f"ERROR: {e}")
