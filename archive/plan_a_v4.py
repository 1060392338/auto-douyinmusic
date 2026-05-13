"""CDP 清理弹窗后 DrissionPage 操作"""
import time, json, requests, websocket
from DrissionPage import ChromiumPage

# 1. 用 /json 获取页面列表+WS URL，处理弹窗
pages = requests.get('http://localhost:9223/json').json()
print(f"处理 {len(pages)} 个页面弹窗:", flush=True)
for p in pages:
    url = p.get('url','')
    title = p.get('title','')[:30]
    print(f"  {title} | {url[:60]}", flush=True)
    
    try:
        ws = websocket.create_connection(p['webSocketDebuggerUrl'], timeout=5)
        ws.settimeout(3)
        ws.send(json.dumps({'id':1, 'method':'Page.getJavaScriptDialogInfo', 'params':{}}))
        r = json.loads(ws.recv())
        if r.get('result',{}).get('hasDialog'):
            msg = r['result'].get('message','')[:50]
            print(f"    ⚠️ 弹窗: {msg}", flush=True)
            ws.send(json.dumps({'id':2, 'method':'Page.handleJavaScriptDialog', 'params':{'accept':True}}))
            json.loads(ws.recv())
            print(f"    ✅ 已处理", flush=True)
        
        # 禁用 onbeforeunload
        ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{
            'expression': 'window.onbeforeunload = null;',
            'returnByValue': True
        }}))
        json.loads(ws.recv())
        ws.close()
    except Exception as e:
        print(f"    ❌ {str(e)[:50]}", flush=True)

time.sleep(2)

# 2. 现在可以用 DrissionPage 了
print("\n连接 DrissionPage...", flush=True)
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;")
print("✅ 弹窗禁用", flush=True)

# 导航到发布页
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

# 智能封面
print("智能封面...", flush=True)
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '智能封面') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
""")
time.sleep(3)

t2 = P.ele('tag:body', timeout=5).text
if '一键生成' in t2:
    print("一键生成封面...", flush=True)
    P.run_js("""
    window.onbeforeunload=null;
    document.querySelectorAll('*').forEach(function(el) {
        if (el.textContent && el.textContent.trim() === '一键生成封面') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.click();
        }
    });
    """)
    time.sleep(5)
    
    t3 = P.ele('tag:body', timeout=5).text
    if '使用封面' in t3:
        print("使用封面...", flush=True)
        P.run_js("""
        window.onbeforeunload=null;
        document.querySelectorAll('*').forEach(function(el) {
            if (el.textContent && el.textContent.trim() === '使用封面') {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.click();
            }
        });
        """)
        time.sleep(3)
        
        # 关闭弹窗
        t3b = P.ele('tag:body', timeout=5).text
        if '使用封面' in t3b:
            print("弹窗未关，取消...", flush=True)
            P.run_js("""
            window.onbeforeunload=null;
            document.querySelectorAll('*').forEach(function(el) {
                var t = (el.textContent || '').trim();
                if ((t === '取消' || t === '关闭') && el.offsetParent !== null) {
                    el.click();
                }
            });
            """)
            time.sleep(3)

# 下一步
print("点击下一步...", flush=True)
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
pages2 = requests.get('http://localhost:9223/json').json()
print(f"页面 ({len(pages2)}):", flush=True)
for p in pages2:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:80]}", flush=True)
    if 'letsign' in url or 'sign' in url.lower():
        print(f"  ✅ 合同页!", flush=True)

try:
    t4 = P.ele('tag:body', timeout=5).text
    print(f"\n底部600: ...{t4[-600:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码']:
        if kw in t4:
            print(f"  ✅ {kw}", flush=True)
except:
    pass

print("\n✅ 完成", flush=True)
