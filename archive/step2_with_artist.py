"""步骤2：先处理艺人信息，再点下一步"""
import time, json, requests, websocket

bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']

# 清理旧页面
b = websocket.create_connection(bws, timeout=5)
for p in requests.get('http://localhost:9223/json').json():
    if 'complete-publish' in p.get('url',''):
        b.send(json.dumps({'id':1, 'method':'Target.closeTarget', 'params':{'targetId':p['id']}}))
        json.loads(b.recv())
        time.sleep(1)
b.close()
time.sleep(2)

# 建新页
b2 = websocket.create_connection(requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl'], timeout=5)
b2.send(json.dumps({'id':1, 'method':'Target.createTarget', 'params':{'url':'about:blank'}}))
tid = json.loads(b2.recv()).get('result',{}).get('targetId')
b2.close()

ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)

def cdp(method, params=None):
    ws.send(json.dumps({'id':int(time.time()*1000)%100000, 'method':method, 'params':params or {}}))
    ws.settimeout(5)
    while True:
        try:
            r = json.loads(ws.recv())
            if 'id' in r:
                return r.get('result')
        except:
            return None

def js(expr):
    r = cdp('Runtime.evaluate', {'expression':expr, 'returnByValue':True})
    return r.get('result',{}).get('value') if r else None

# 导航到发布页
cdp('Page.navigate', {'url':'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'})
time.sleep(8)
js('window.onbeforeunload=null;')

# --- 第1次 "下一步" 到步骤2 ---
print("1. 步骤1→2", flush=True)
js('''
document.querySelectorAll('button').forEach(function(b) {
    var t = (b.textContent || '').trim();
    if (t === '下一步' && b.offsetParent !== null) {
        b.scrollIntoView({behavior:'instant',block:'center'});
        b.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            b.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(5)

t = js('document.body.innerText')
print(f"   文本:{len(t) if t else '?'}", flush=True)

# --- 处理艺人信息 ---
if t and '有主页链接' in t:
    print("2. 艺人信息: 有主页链接→无主页链接", flush=True)
    js('''
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '有主页链接') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus(); el.click();
        }
    });
    ''')
    time.sleep(2)
    js('''
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '无主页链接') {
            el.focus(); el.click();
        }
    });
    ''')
    time.sleep(2)
    print("   ✅ 无主页链接", flush=True)

# --- 第2次 "下一步" 到步骤3 ---
print("3. 步骤2→3", flush=True)
# 先滚动到可见
js('window.scrollTo(0, document.body.scrollHeight);')
time.sleep(2)

js('''
document.querySelectorAll('button').forEach(function(b) {
    var t = (b.textContent || '').trim();
    if (t === '下一步' && b.offsetParent !== null) {
        b.scrollIntoView({behavior:'instant',block:'center'});
        b.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            b.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(8)

t2 = js('document.body.innerText')
print(f"   文本:{len(t2) if t2 else '?'}", flush=True)

# 检查
if t2:
    for kw in ['批量签署','意愿认证','获取验证码','合同签署','签署协议（1）']:
        if kw in t2:
            print(f"   ✅ {kw}", flush=True)

pages = requests.get('http://localhost:9223/json').json()
for p in pages:
    url = p.get('url','')
    if 'letsign' in url:
        print(f"   ✅ 合同页! {url[:100]}", flush=True)

# DOM 检查
dom = js('''
(function() {
    var info = {visibleBtns: [], iframes: [], text: document.body.innerText.length};
    document.querySelectorAll('button').forEach(function(b) {
        var t = (b.textContent || '').trim();
        if (t && b.offsetParent !== null) info.visibleBtns.push(t.substring(0,20));
    });
    document.querySelectorAll('iframe').forEach(function(f) {
        if (f.src) info.iframes.push(f.src.substring(0,100));
    });
    return JSON.stringify(info);
})();
''')
print(f"\nDOM: {dom}", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
