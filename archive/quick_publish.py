"""快速发布流程"""
import time, json, requests, websocket

def cdp(ws, method, params=None, timeout=5):
    cid = int(time.time()*1000)%100000
    ws.send(json.dumps({'id':cid, 'method':method, 'params':params or {}}))
    ws.settimeout(timeout)
    while True:
        try:
            r = json.loads(ws.recv())
            if r.get('id')==cid:
                return r.get('result') if 'result' in r else r.get('error')
        except:
            return None

def js(ws, expr):
    r = cdp(ws, 'Runtime.evaluate', {'expression':expr, 'returnByValue':True})
    return r.get('result',{}).get('value') if r else None

# 创建新页面
bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)
r = cdp(b, 'Target.createTarget', {'url':'about:blank'})
b.close()
tid = r.get('targetId') if r else None
if not tid:
    print("❌ 创建失败", flush=True)
    exit()

# 连接页面
ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)

# 导航到发布页
cdp(ws, 'Page.navigate', {'url':'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'})
time.sleep(8)

text = js(ws, 'document.body.innerText')
if not text or len(text)<100:
    print("❌ 加载失败", flush=True)
    ws.close()
    exit()

print(f"✅ 发布页加载, 文本长度:{len(text)}", flush=True)

# 艺人信息
if '有主页链接' in text:
    js(ws, '''document.querySelectorAll('*').forEach(e=>{if(e.textContent&&e.textContent.trim()==='有主页链接'){e.scrollIntoView({behavior:'instant',block:'center'});e.focus();e.click();}})''')
    time.sleep(2)
    js(ws, '''document.querySelectorAll('*').forEach(e=>{if(e.textContent&&e.textContent.trim()==='无主页链接'){e.focus();e.click();}})''')
    time.sleep(2)
    print("✅ 无主页链接", flush=True)

# 智能封面
js(ws, '''document.querySelectorAll('*').forEach(e=>{var t=(e.textContent||'').trim();if(t==='智能封面'){e.scrollIntoView({behavior:'instant',block:'center'});e.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(ev=>e.dispatchEvent(new PointerEvent(ev,{bubbles:!0,cancelable:!0})));}})''')
time.sleep(3)
t2 = js(ws, 'document.body.innerText')
if t2 and '一键生成' in t2:
    print("✅ 一键生成封面", flush=True)
    js(ws, '''document.querySelectorAll('*').forEach(e=>{if(e.textContent&&e.textContent.trim()==='一键生成封面'){e.scrollIntoView({behavior:'instant',block:'center'});e.click();}})''')
    time.sleep(5)
    t3 = js(ws, 'document.body.innerText')
    if t3 and '使用封面' in t3:
        js(ws, '''document.querySelectorAll('*').forEach(e=>{if(e.textContent&&e.textContent.trim()==='使用封面'){e.scrollIntoView({behavior:'instant',block:'center'});e.click();}})''')
        time.sleep(3)
        print("✅ 封面已设置", flush=True)

# 下一步
print("点击下一步...", flush=True)
js(ws, '''document.querySelectorAll('*').forEach(e=>{var t=(e.textContent||'').trim();if(t==='下一步'){e.scrollIntoView({behavior:'instant',block:'center'});e.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(ev=>e.dispatchEvent(new PointerEvent(ev,{bubbles:!0,cancelable:!0})));}})''')
time.sleep(8)

# 检查页面
pages = requests.get('http://localhost:9223/json').json()
print(f"\n页面 ({len(pages)}):", flush=True)
for p in pages:
    u = p.get('url','')
    print(f"  {p['title'][:30]} | {u[:80]}", flush=True)
    if 'letsign' in u or 'sign' in u.lower():
        print(f"  ✅ 合同页! WS:{p['webSocketDebuggerUrl'][:50]}", flush=True)

t4 = js(ws, 'document.body.innerText')
if t4:
    print(f"\n底部500: ...{t4[-500:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','合同签署']:
        if kw in t4:
            print(f"  ✅ {kw}", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
