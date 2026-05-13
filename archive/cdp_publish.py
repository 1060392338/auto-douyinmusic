"""CDP websocket 完整发布流程"""
import time, json, requests, websocket

def cdp(ws, method, params=None, timeout=5):
    cmd_id = int(time.time() * 1000) % 100000
    ws.send(json.dumps({'id': cmd_id, 'method': method, 'params': params or {}}))
    ws.settimeout(timeout)
    while True:
        try:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd_id:
                if 'error' in resp:
                    return {'error': resp['error']}
                return resp.get('result')
        except websocket.WebSocketTimeoutException:
            return None

def js(ws, expr):
    """执行JS返回结果"""
    r = cdp(ws, 'Runtime.evaluate', {
        'expression': expr, 'returnByValue': True, 'awaitPromise': True
    }, timeout=10)
    if r and 'result' in r:
        return r['result'].get('value')
    return None

# 获取发布页 WS
pages = requests.get('http://localhost:9223/json').json()
pub = [p for p in pages if 'complete-publish' in p.get('url', '')]
if not pub:
    # 开新页
    print("无发布页，创建...", flush=True)
    ver = requests.get('http://localhost:9223/json/version').json()
    bws = ver['webSocketDebuggerUrl']
    ws_b = websocket.create_connection(bws, timeout=5)
    r = cdp(ws_b, 'Target.createTarget', {
        'url': 'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'
    })
    ws_b.close()
    if not r or 'targetId' not in r:
        print("❌ 创建页面失败", flush=True)
        exit()
    target_id = r['targetId']
    ws_url = f'ws://localhost:9223/devtools/page/{target_id}'
    print(f"新页面WS: {ws_url}", flush=True)
else:
    ws_url = pub[0]['webSocketDebuggerUrl']
    print(f"现有发布页WS: {ws_url[:60]}...", flush=True)

ws = websocket.create_connection(ws_url, timeout=10)
ws.settimeout(10)

# 激活页面
cdp(ws, 'Page.bringToFront')
time.sleep(3)

# 重试获取文本
text = None
for _ in range(5):
    time.sleep(2)
    text = js(ws, 'document.body.innerText')
    if text and len(text) > 100:
        break

if not text or len(text) < 100:
    print("❌ 页面加载失败", flush=True)
    ws.close()
    exit()

print(f"页面文本长度: {len(text)}", flush=True)

# 1. 艺人信息
if '有主页链接' in text:
    print("1. 艺人信息...", flush=True)
    js(ws, '''
    document.querySelectorAll('*').forEach(function(el) {
        if (el.textContent && el.textContent.trim() === '有主页链接') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus(); el.click();
        }
    });
    ''')
    time.sleep(2)
    js(ws, '''
    document.querySelectorAll('*').forEach(function(el) {
        if (el.textContent && el.textContent.trim() === '无主页链接') {
            el.focus(); el.click();
        }
    });
    ''')
    time.sleep(2)
    print("   ✅ 无主页链接", flush=True)

# 2. 智能封面
print("2. 智能封面...", flush=True)
js(ws, '''
document.querySelectorAll('*').forEach(function(el) {
    if (el.textContent && el.textContent.trim() === '智能封面') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(3)

text2 = js(ws, 'document.body.innerText')
if text2 and '一键生成' in text2:
    print("   一键生成封面...", flush=True)
    js(ws, '''
    document.querySelectorAll('*').forEach(function(el) {
        if (el.textContent && el.textContent.trim() === '一键生成封面') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.click();
        }
    });
    ''')
    time.sleep(5)
    
    text3 = js(ws, 'document.body.innerText')
    if text3 and '使用封面' in text3:
        print("   使用封面...", flush=True)
        js(ws, '''
        document.querySelectorAll('*').forEach(function(el) {
            if (el.textContent && el.textContent.trim() === '使用封面') {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.click();
            }
        });
        ''')
        time.sleep(3)
        print("   ✅ 封面已设置！", flush=True)

# 3. 下一步
print("3. 点击下一步...", flush=True)
js(ws, '''
document.querySelectorAll('*').forEach(function(el) {
    var t = el.textContent;
    if (t && t.trim() === '下一步') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(8)

# 检查是否有新页面
pages2 = requests.get('http://localhost:9223/json').json()
print(f"\n当前页面 ({len(pages2)}):", flush=True)
for p in pages2:
    url = p.get('url', '')
    print(f"  {p['title'][:30]} | {url[:80]}", flush=True)
    if 'letsign' in url or 'sign' in url.lower():
        print(f"  ✅ 合同页!", flush=True)

# 查看当前页底部
text4 = js(ws, 'document.body.innerText')
if text4:
    print(f"\n底部400字: ...{text4[-400:]}", flush=True)
    for kw in ['批量签署', '意愿认证', '获取验证码', '合同签署', '授权信息', '签署协议（1）']:
        if kw in text4:
            print(f"  ✅ {kw}", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
