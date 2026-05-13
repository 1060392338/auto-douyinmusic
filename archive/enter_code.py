"""填入验证码并确认签署"""
import time, json, requests, websocket

# 找 letsign 页面
pages = requests.get('http://localhost:9223/json').json()
letsign = None
for p in pages:
    if 'letsign' in p.get('url',''):
        letsign = p
        break

if not letsign:
    print("❌ 找不到 letsign 页", flush=True)
    exit()

ws = websocket.create_connection(letsign['webSocketDebuggerUrl'], timeout=10)

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

# 激活页面
cdp('Page.bringToFront')
time.sleep(2)

# 1. 填入验证码
print("填入验证码...", flush=True)
code = "250081"
js(f'''
document.querySelectorAll('input').forEach(function(inp) {{
    var ph = (inp.placeholder || '');
    if (ph.indexOf('验证码') >= 0 || ph.indexOf('数字') >= 0) {{
        // 用 nativeSetter 触发 React 事件
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, '{code}');
        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
        inp.dispatchEvent(new Event('change', {{bubbles: true}}));
    }}
}});
''')
time.sleep(2)
print("✅ 验证码已填入", flush=True)

# 2. 点击确定
print("点击确定...", flush=True)
js('''
document.querySelectorAll('button').forEach(function(b) {
    if (b.textContent.trim() === '确定') {
        b.scrollIntoView({behavior:'instant',block:'center'});
        b.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            b.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(5)

# 3. 查看结果
text = js('document.body.innerText')
print(f"\n签署后文本 (前500):", flush=True)
print(text[:500] if text else 'None', flush=True)

if text:
    for kw in ['签署成功','处理中','已签署','完成','成功']:
        if kw in text:
            print(f"✅ {kw}", flush=True)

# 获取所有页面
pages2 = requests.get('http://localhost:9223/json').json()
print(f"\n所有页面:", flush=True)
for p in pages2:
    print(f"  {p['title'][:30]} | {p.get('url','')[:80]}", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
