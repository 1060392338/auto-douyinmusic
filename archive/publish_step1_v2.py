"""蝉声漫旧夏 - 发布 Step 1 v2: 点击卡片触发"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)

# 方式1: 点击卡片上所有包含发行全曲的元素
P.run_js("""
(function() {
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent.trim() === '发行全曲') {
            // 检查它是否在蝉声漫旧夏的卡片内
            var parent = all[i].parentElement;
            while (parent) {
                if (parent.textContent.indexOf('蝉声漫旧夏') >= 0) {
                    console.log('找到发行全曲元素:', all[i].tagName, all[i].className);
                    // 点击
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                        all[i].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                    });
                    return 'clicked';
                }
                parent = parent.parentElement;
            }
        }
    }
    return 'not found';
})();
""")
time.sleep(5)

print(f"URL: {P.url}", flush=True)
body = P.ele('tag:body').text

if 'complete-publish' in P.url or ('歌曲信息' in body and '下一步' in body):
    print("✅ 已进入发布表单!", flush=True)
    print(body[:2000], flush=True)
else:
    print("❌ 未进入，尝试方式2: 直接发 click 事件到卡片", flush=True)
    # 方式2: 点击卡片本身（data-work-id 的卡片）
    P.run_js("""
    (function() {
        var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
        for (var i = 0; i < cards.length; i++) {
            if (cards[i].textContent.indexOf('蝉声漫旧夏') >= 0) {
                cards[i].scrollIntoView({behavior:'instant', block:'center'});
                // 直接 dispatch 到卡片
                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                    cards[i].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                });
                return 'card_clicked';
            }
        }
        return 'card_not_found';
    })();
    """)
    time.sleep(5)
    
    print(f"URL after card click: {P.url}", flush=True)
    body2 = P.ele('tag:body').text
    if 'complete-publish' in P.url or ('歌曲信息' in body2 and '下一步' in body2):
        print("✅ 方式2成功!", flush=True)
        print(body2[:2000], flush=True)
    else:
        print("❌ 方式2也失败", flush=True)
        # 方式3: 从菜单的「发行」选项
        print("尝试方式3: 三点菜单...", flush=True)
        P.run_js("""
        (function() {
            var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
            for (var i = 0; i < cards.length; i++) {
                if (cards[i].textContent.indexOf('蝉声漫旧夏') >= 0) {
                    // 找三点菜单
                    var menu = cards[i].querySelector('[class*="menuMoreWrapper"]') || 
                              cards[i].querySelector('[data-dropdown-trigger-id]');
                    if (menu) {
                        menu.scrollIntoView({behavior:'instant', block:'center'});
                        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                            menu.dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                        });
                        return 'menu_clicked';
                    }
                    return 'no_menu';
                }
            }
            return 'no_card';
        })();
        """)
        time.sleep(3)
        body3 = P.ele('tag:body').text
        print(f"三点菜单后文本含发行: {'发行' in body3}", flush=True)
        print(body3[:1500], flush=True)
