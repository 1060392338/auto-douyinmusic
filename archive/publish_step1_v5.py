"""直接用 CDP 处理弹窗 + 点击发行全曲"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

print("1. 检查当前页面", flush=True)
try:
    print(f"  当前URL: {P.url}", flush=True)
except:
    print("  无法获取URL", flush=True)

# 直接用 CDP 调用来处理弹窗
print("2. 用 CDP 处理弹窗", flush=True)
try:
    result = P.run_cdp('Page.handleJavaScriptDialog', accept=True)
    print(f"  CDP accept dialog: {result}", flush=True)
except Exception as e:
    print(f"  CDP dialog error: {e}", flush=True)

# 导航 - 尝试直接用 CDP
print("3. 导航到资产页", flush=True)
try:
    P.run_cdp('Page.navigate', url='https://music.douyin.com/studio/assets')
    print("  CDP navigate done", flush=True)
except Exception as e:
    print(f"  CDP navigate error: {e}", flush=True)
    # 回退到 JS 导航
    try:
        P.run_js("window.onbeforeunload=null;window.location.href='https://music.dyin.com/studio/assets';")
    except:
        pass

time.sleep(5)

# 再处理一次
try:
    P.run_cdp('Page.handleJavaScriptDialog', accept=True)
except:
    pass

print(f"4. URL: {P.url}", flush=True)

# 获取页面结构
print("5. 点击发行全曲", flush=True)
try:
    result = P.run_cdp('Runtime.evaluate', expression="""
    (function() {
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent && all[i].textContent.trim() === '发行全曲') {
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
    print(f"  执行结果: {result}", flush=True)
except Exception as e:
    print(f"  evaluate error: {e}", flush=True)

time.sleep(5)
print(f"6. 点击后URL: {P.url}", flush=True)
body = P.ele('tag:body').text
print(f"  页面: {body[:1500]}", flush=True)
