"""点下一步，检查 DOM 变化"""
import time, json, requests, websocket

bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)
for p in requests.get('http://localhost:9223/json').json():
    if 'complete-publish' in p.get('url',''):
        b.send(json.dumps({'id':1, 'method':'Target.closeTarget', 'params':{'targetId':p['id']}}))
        json.loads(b.recv())
        time.sleep(1)
b.close()
time.sleep(2)

b2 = websocket.create_connection(requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl'], timeout=5)
b2.send(json.dumps({'id':1, 'method':'Target.createTarget', 'params':{'url':'about:blank'}}))
r = json.loads(b2.recv())
b2.close()
tid = r.get('result',{}).get('targetId')

ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
def cdp(method, params=None, timeout=5):
    ws.send(json.dumps({'id':int(time.time()*1000)%100000, 'method':method, 'params':params or {}}))
    ws.settimeout(timeout)
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

cdp('Page.navigate', {'url':'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'})
time.sleep(8)
js('window.onbeforeunload=null;')

text = js('document.body.innerText')
print(f"✅ Step1 页面, 文本:{len(text)}", flush=True)

# 点下一步
print("点击下一步...", flush=True)
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

text2 = js('document.body.innerText')
print(f"点击后文本: {len(text2) if text2 else '?'}", flush=True)

# 分析 DOM 变化
dom = js('''
(function() {
    var info = {visibleBtns: [], text: document.body.innerText.length};
    document.querySelectorAll('button').forEach(function(b) {
        var t = (b.textContent || '').trim();
        if (t && b.offsetParent !== null) info.visibleBtns.push(t);
    });
    return JSON.stringify(info);
})();
''')
print(f"\n可见按钮: {dom}", flush=True)

# 检查是否进入步骤2/3
if text2:
    for kw in ['独家授权','签署协议','授权信息','上一步','下一步','批量签署','意愿认证','授权比例']:
        if kw in text2:
            print(f"  ✅ {kw}", flush=True)

# 如果进入步骤2，再点下一步
if text2 and ('独家授权' in text2 or '授权信息' in text2):
    print("\n步骤2可见！再点一次下一步...", flush=True)
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
    
    text3 = js('document.body.innerText')
    dom2 = js('''
    (function() {
        var info = {visibleBtns: [], iframes: []};
        document.querySelectorAll('button').forEach(function(b) {
            var t = (b.textContent || '').trim();
            if (t && b.offsetParent !== null) info.visibleBtns.push(t);
        });
        document.querySelectorAll('iframe').forEach(function(f) {
            if (f.src) info.iframes.push(f.src.substring(0,100));
        });
        return JSON.stringify(info);
    })();
    ''')
    print(f"二次点击后可见按钮: {dom2}", flush=True)
    
    pages = requests.get('http://localhost:9223/json').json()
    for p in pages:
        if 'letsign' in p.get('url',''):
            print(f"  ✅ 合同页!", flush=True)

ws.close()
print("\n✅", flush=True)
