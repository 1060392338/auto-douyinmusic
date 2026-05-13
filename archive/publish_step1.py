"""蝉声漫旧夏 - 发布流程 Step 1: 点击发行全曲进入表单"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 确保在资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)

# 找到蝉声漫旧夏的卡片，点击发行全曲
P.run_js("""
(function() {
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for (var i = 0; i < cards.length; i++) {
        if (cards[i].textContent.indexOf('蝉声漫旧夏') >= 0) {
            // 找到发行全曲文本元素
            var all = cards[i].querySelectorAll('*');
            for (var j = 0; j < all.length; j++) {
                if (all[j].textContent.trim() === '发行全曲') {
                    all[j].scrollIntoView({behavior:'instant', block:'center'});
                    setTimeout(function() {
                        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                            all[j].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                        });
                    }, 300);
                    return;
                }
            }
        }
    }
    console.log('没找到发行全曲');
})();
""")
time.sleep(5)

print(f"当前URL: {P.url}", flush=True)
body = P.ele('tag:body').text
print(f"页面文本 (前2000):", flush=True)
print(body[:2000], flush=True)

# 检查是否进入了发布表单
if 'complete-publish' in P.url:
    print("\n✅ 已进入发布表单!", flush=True)
elif '发行' in body and ('下一步' in body or '歌曲信息' in body or '授权' in body):
    print("\n✅ 可能已进入发布表单（SPA路由）", flush=True)
else:
    print("\n❌ 未进入发布表单", flush=True)
