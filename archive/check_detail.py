"""点击查看详情看状态"""
import time, json, requests, websocket

bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)
for p in requests.get('http://localhost:9223/json').json():
    if '/studio/assets' in p.get('url',''):
        b.send(json.dumps({'id':1, 'method':'Target.closeTarget', 'params':{'targetId':p['id']}}))
        json.loads(b.recv())
        time.sleep(1)
b.close()
time.sleep(2)

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

# 导航到资产页
cdp('Page.navigate', {'url':'https://music.douyin.com/studio/assets'})
time.sleep(8)
js('window.onbeforeunload=null;')

# 找到蝉声漫旧夏的"查看详情"并点击
print("点击查看详情...", flush=True)
js('''
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '查看详情') {
        // 检查是否在蝉声漫旧夏卡片内
        var parent = el.parentElement;
        while (parent) {
            if (parent.textContent.indexOf('蝉声漫旧夏') >= 0) {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.focus();
                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                    el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
                });
                return;
            }
            parent = parent.parentElement;
        }
    }
});
''')
time.sleep(5)

text = js('document.body.innerText')
print(f"点击后文本: {text[:1000] if text else 'None'}", flush=True)
if text:
    for kw in ['审核中','审核通过','已发行','发行成功','已提交','处理中','已驳回','已发布','蝉声漫旧夏']:
        if kw in text:
            idx = text.find(kw)
            start = max(0, idx-30)
            end = min(len(text), idx+80)
            print(f"✅ {kw}: ...{text[start:end]}...", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
