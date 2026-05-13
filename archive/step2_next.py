"""继续第二步：艺人信息+下一步到签署"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;")
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)
P.run_js("window.onbeforeunload=null;")

body = None
for _ in range(5):
    time.sleep(2)
    try:
        body = P.ele('tag:body', timeout=5)
        if body and len(body.text) > 200:
            break
    except:
        P.run_js("window.onbeforeunload=null;")

if not body:
    print("❌ 加载失败", flush=True)
    exit()

text = body.text
print(f"✅ 发布页, 文本长度:{len(text)}", flush=True)
print(f"当前步骤:", flush=True)
for kw in ['独家授权','签署协议','授权信息','有主页链接','智能封面','下一步']:
    print(f"  {kw}: {'✅' if kw in text else '❌'}", flush=True)

# 关闭任何打开的弹窗
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if ((t === '取消' || t === '关闭') && el.offsetParent !== null) {
        el.click();
    }
});
""")
time.sleep(2)

# 艺人信息
if '有主页链接' in text:
    print("\n艺人信息: 有主页链接→无主页链接", flush=True)
    P.run_js("""
    window.onbeforeunload=null;
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '有主页链接') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus(); el.click();
        }
    });
    """)
    time.sleep(2)
    P.run_js("""
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '无主页链接') {
            el.focus(); el.click();
        }
    });
    """)
    time.sleep(2)
    print("   ✅ 无主页链接", flush=True)

# 点击下一步（从授权步骤到签署协议）
print("\n点击下一步到签署协议...", flush=True)
P.run_js("window.onbeforeunload=null;window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '下一步' && el.offsetParent !== null) {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
""")
time.sleep(8)

print(f"URL: {P.url[:80]}", flush=True)

# 检查所有页面
pages = requests.get('http://localhost:9223/json').json()
print(f"\n所有页面 ({len(pages)}):", flush=True)
for p in pages:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:100]}", flush=True)
    if 'letsign' in url:
        print(f"  ✅ 合同页! WS:{p['webSocketDebuggerUrl'][:60]}", flush=True)

try:
    t2 = P.ele('tag:body', timeout=5).text
    print(f"\n页面底部500: ...{t2[-500:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','letsign','签署协议（1）','已签署']:
        if kw in t2:
            print(f"  ✅ {kw}", flush=True)
except:
    pass

print("\n✅ 完成", flush=True)
