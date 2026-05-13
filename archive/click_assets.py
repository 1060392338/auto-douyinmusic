"""从 studio 内点击 我的资产"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(6)

# 找到「我的资产」导航项并点击
navs = P.eles('xpath://div[contains(@class,"navigation-item-wrapper")]')
for n in navs:
    t = n.text.strip()
    if '资产' in t:
        print(f"点击: {t}", flush=True)
        # 用 JS dispatchEvent 点击
        P.run_js("""
(function() {
    var navs = document.querySelectorAll('[class*="navigation-item-wrapper"]');
    for (var i = 0; i < navs.length; i++) {
        if (navs[i].textContent.trim().includes('资产')) {
            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                navs[i].dispatchEvent(new PointerEvent(ev, {bubbles: true, cancelable: true}));
            });
            return;
        }
    }
})();
""")
        time.sleep(5)
        break

print(f"当前URL: {P.url}", flush=True)
body = P.ele('tag:body').text
print(f"资产页文本长度: {len(body)}", flush=True)
print(f"资产页内容:", flush=True)
print(body[:3000], flush=True)

# 搜索关键信息
for kw in ['蝉声漫旧夏', '发行全曲', '已发布', '已发行', '审核', '新项目']:
    if kw in body:
        idx = body.find(kw)
        start = max(0, idx-30)
        end = min(len(body), idx+80)
        print(f"✅ {kw} -> ...{body[start:end]}...", flush=True)
    else:
        print(f"❌ {kw}", flush=True)
