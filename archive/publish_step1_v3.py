"""处理弹窗后点击发行全曲"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 先处理可能存在的弹窗
for _ in range(3):
    try:
        P.handle_alert(accept=True)
        time.sleep(1)
        print("处理了一个弹窗", flush=True)
    except:
        break

# 导航到资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)

# 再处理一次弹窗
for _ in range(3):
    try:
        P.handle_alert(accept=True)
        time.sleep(1)
        print("又处理了一个弹窗", flush=True)
    except:
        break

print(f"URL: {P.url}", flush=True)
body = P.ele('tag:body').text

# 找到「发行全曲」并点击
P.run_js("""
(function() {
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent.trim() === '发行全曲') {
            var parent = all[i].parentElement;
            while (parent) {
                if (parent.textContent.indexOf('蝉声漫旧夏') >= 0) {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                        all[i].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                    });
                    return 'clicked_' + all[i].tagName;
                }
                parent = parent.parentElement;
            }
        }
    }
    return 'not_found';
})();
""")
time.sleep(5)

print(f"点击后URL: {P.url}", flush=True)
body2 = P.ele('tag:body').text
print(f"页面文本 (前2000):", flush=True)
print(body2[:2000], flush=True)

# 检查是否进入发布表单
if 'complete-publish' in P.url or 'console' in P.url:
    print("\n✅ 进入了发布表单!", flush=True)
elif '歌曲信息' in body2 or '下一步' in body2 or '上传' in body2:
    print("\n✅ 可能进入了发布表单!", flush=True)
else:
    print("\n❌ 未进入发布表单", flush=True)
