#!/usr/bin/env python3
"""全流程发布脚本 - 无alert处理版"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)
print("=" * 50)
print("STEP 1: 在资产页")
print("=" * 50)
print("URL:", P.url[:60])

# 点击蝉声漫旧夏的"发行全曲"
P.run_js("""
window.onbeforeunload = null;
(function() {
    var cards = document.querySelectorAll("[class*='assetItemWrapper']");
    for (var i = 0; i < cards.length; i++) {
        if (cards[i].textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f') >= 0) {
            var all = cards[i].querySelectorAll('*');
            for (var j = 0; j < all.length; j++) {
                if (all[j].textContent.trim() === '\u53d1\u884c\u5168\u66f2') {
                    all[j].scrollIntoView({behavior:'instant', block:'center'});
                    setTimeout(function(){ all[j].click(); }, 300);
                    return;
                }
            }
        }
    }
})();
""")
time.sleep(6)
print("点击后URL:", P.url[:80])

if 'complete-publish' in P.url:
    print("✅ 进入发布表单")
    print("=" * 50)
    print("STEP 2: 下一步 → 合同签署")
    print("=" * 50)
    
    # 滚动到底部
    P.run_js("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # 点击底部的「下一步」
    P.run_js("""
    (function() {
        var btns = document.querySelectorAll('button');
        var lastNext = null;
        for (var i = 0; i < btns.length; i++) {
            if (btns[i].textContent.trim() === '\u4e0b\u4e00\u6b65') {
                lastNext = btns[i];
            }
        }
        if (lastNext) {
            lastNext.scrollIntoView({behavior:'instant', block:'center'});
            lastNext.click();
        }
    })();
    """)
    time.sleep(5)
    print("下一步后URL:", P.url[:80])
    
    # 打开letsign合同
    P.run_js("""
    (function() {
        var iframes = document.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            var src = iframes[i].src || '';
            if (src.indexOf('letsign') >= 0) {
                window.open(src);
                return;
            }
        }
    })();
    """)
    time.sleep(5)
    
    # 切到letsign
    targets = P.run_cdp('Target.getTargets')
    letsign_id = None
    for t in targets.get('targetInfos', []):
        url = t.get('url', '')
        if 'letsign.com/v2/open/sign' in url and t.get('type') == 'page':
            letsign_id = t['targetId']
            break
    
    if letsign_id:
        P.run_cdp('Target.activateTarget', targetId=letsign_id)
        time.sleep(5)
        print("✅ 进入letsign合同页")
        print("标题:", P.title[:40])
        
        # 点击批量签署
        P.run_js("""
        (function() {
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.trim() === '\u6279\u91cf\u7b7e\u7f72') {
                    btns[i].scrollIntoView({behavior:'instant', block:'center'});
                    btns[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(3)
        print("✅ 已点批量签署")
        
        # 点击获取验证码
        P.run_js("""
        (function() {
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.trim() === '\u83b7\u53d6\u9a8c\u8bc1\u7801') {
                    btns[i].scrollIntoView({behavior:'instant', block:'center'});
                    btns[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(2)
        print("=" * 50)
        print("STEP 3: 等待验证码...")
        print("=" * 50)
        print("\n陛下，验证码已发送！请查收后发给我！")
    else:
        print("❌ 找不到letsign")
else:
    print("❌ 未进入发布表单，URL:", P.url[:80])
