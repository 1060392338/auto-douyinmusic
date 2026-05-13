#!/usr/bin/env python3
"""全流程发布脚本: 资产页→发行全曲→签署→等验证码"""
import time, os
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

# 清除弹窗
for _ in range(5):
    try:
        P.handle_alert(accept=True)
        time.sleep(0.5)
    except:
        break

print("=" * 50)
print("STEP 1: 导航到资产页")
print("=" * 50)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)
print("当前URL:", P.url[:60])

print("\n" + "=" * 50)
print("STEP 2: 点击「蝉声漫旧夏」的「发行全曲」")
print("=" * 50)
P.run_js("""
(function() {
    window.onbeforeunload = null;
    var cards = document.querySelectorAll("[class*='assetItemWrapper']");
    for (var i = 0; i < cards.length; i++) {
        if (cards[i].textContent.indexOf('\u8749\u58f0\u6f2b\u65e7\u590f') >= 0) {
            var all = cards[i].querySelectorAll('*');
            for (var j = 0; j < all.length; j++) {
                if (all[j].textContent.trim() === '\u53d1\u884c\u5168\u66f2') {
                    all[j].scrollIntoView({behavior:'instant', block:'center'});
                    all[j].click();
                    return;
                }
            }
        }
    }
})();
""")
time.sleep(5)
print("点击后URL:", P.url[:80])

if 'complete-publish' in P.url:
    print("\n✅ 已进入发布表单！")

    print("\n" + "=" * 50)
    print("STEP 3: 检查预填信息，点击下一步")
    print("=" * 50)
    
    # 检查歌曲标题是否已填
    title_input = P.run_js("""
    (function() {
        var inps = document.querySelectorAll('input');
        for (var i = 0; i < inps.length; i++) {
            if (inps[i].placeholder == '\u8bf7\u8f93\u5165') {
                return inps[i].value || 'EMPTY';
            }
        }
        return 'NOT_FOUND';
    })();
    """)
    print(f"歌曲标题: {title_input}")
    
    # 滚动到底部
    P.run_js("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # 点击底部「下一步」
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

    print("\n" + "=" * 50)
    print("STEP 4: 进入合同签署")
    print("=" * 50)
    
    # 找letsign iframe - 打开新标签页
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
    
    # 获取所有tab
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
        print(f"✅ 已切换到letsign页，标题: {P.title}")
        
        # 点击「批量签署」
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
        time.sleep(4)
        print("✅ 已点击批量签署")
        
        # 点击「获取验证码」
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
        print("\n" + "=" * 50)
        print("STEP 5: 等待陛下发送验证码...")
        print("=" * 50)
        print("\n验证码已发送到手机，请查收后发给我！")
    else:
        print("❌ 找不到letsign页面")
else:
    print("❌ 未进入发布表单")
