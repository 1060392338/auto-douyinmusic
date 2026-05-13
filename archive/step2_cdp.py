"""CDP 清理弹窗 + 继续下一步"""
import time, json, requests, websocket
from DrissionPage import ChromiumPage

# 1. CDP 先处理所有弹窗
pages = requests.get('http://localhost:9223/json').json()
print(f"处理 {len(pages)} 页面弹窗...", flush=True)
for p in pages:
    url = p.get('url','')
    if not url or 'sw.js' in url:
        continue
    try:
        ws = websocket.create_connection(p['webSocketDebuggerUrl'], timeout=5)
        ws.settimeout(3)
        ws.send(json.dumps({'id':1, 'method':'Page.getJavaScriptDialogInfo', 'params':{}}))
        r = json.loads(ws.recv())
        if r.get('result',{}).get('hasDialog'):
            print(f"  处理弹窗: {p['title'][:30]}", flush=True)
            ws.send(json.dumps({'id':2, 'method':'Page.handleJavaScriptDialog', 'params':{'accept':True}}))
            json.loads(ws.recv())
        # 禁用
        ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{
            'expression': 'window.onbeforeunload = null;', 'returnByValue': True
        }}))
        json.loads(ws.recv())
        ws.close()
    except Exception as e:
        print(f"  ⚠️ {p['title'][:20]}: {str(e)[:40]}", flush=True)

time.sleep(2)

# 2. DrissionPage 连接
print("\n连接 DrissionPage...", flush=True)
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")
print("✅ 弹窗禁用", flush=True)

# 3. 导航到发布页
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

# 4. 关闭弹窗
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

# 5. 艺人信息
if '有主页链接' in text:
    print("艺人信息: 有主页链接→无主页链接", flush=True)
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

# 6. 滚动到底部
P.run_js("window.onbeforeunload=null;window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# 7. 下一步
print("点击下一步...", flush=True)
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

# 8. 检查
print(f"\nURL: {P.url[:80]}", flush=True)
pages2 = requests.get('http://localhost:9223/json').json()
print(f"页面 ({len(pages2)}):", flush=True)
for p in pages2:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:100]}", flush=True)
    if 'letsign' in url:
        print(f"  ✅ 合同页!", flush=True)

try:
    t2 = P.ele('tag:body', timeout=5).text
    print(f"\n底部600: ...{t2[-600:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','letsign']:
        if kw in t2:
            print(f"  ✅ {kw}", flush=True)
except:
    pass

print("\n✅ 完成", flush=True)
