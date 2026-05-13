"""用 CDP 处理弹窗 + 点击发行全曲"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 用 CDP 处理任何弹窗（非阻塞）
try:
    P.run_cdp('Page.handleJavaScriptDialog', accept=True)
    print("CDP 处理了弹窗", flush=True)
except:
    print("没有弹窗", flush=True)

# 导航到资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(6)

try:
    P.run_cdp('Page.handleJavaScriptDialog', accept=True)
    print("CDP 又处理了弹窗", flush=True)
except:
    pass

print(f"URL: {P.url}", flush=True)
body_text = P.ele('tag:body').text
print(f"文本长度: {len(body_text)}", flush=True)

# 点击发行全曲 - 用 querySelectorAll 找文本
P.run_js("""
(function() {
    var all = document.querySelectorAll('*');
    for (var i = 0; i < all.length; i++) {
        if (all[i].textContent.trim() === '发行全曲') {
            var p = all[i].parentElement;
            while (p) {
                if (p.textContent.indexOf('蝉声漫旧夏') >= 0) {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                        all[i].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
                    });
                    return 'OK';
                }
                p = p.parentElement;
            }
        }
    }
    return 'NOT_FOUND';
})();
""")
time.sleep(5)

print(f"点击后URL: {P.url}", flush=True)
body2 = P.ele('tag:body').text
print(f"页面 (前2000):", flush=True)
print(body2[:2000], flush=True)
