"""强制重置发布页 + 快速操作"""
import time, json, requests, websocket

# 1. 获取 browser WS
ver = requests.get('http://localhost:9223/json/version').json()
bws = ver['webSocketDebuggerUrl']
print(f"Browser WS: {bws}", flush=True)

# 2. 列出所有目标
ws_b = websocket.create_connection(bws, timeout=5)

# 获取所有 target
cmd_id = 1
ws_b.send(json.dumps({'id': cmd_id, 'method': 'Target.getTargets', 'params': {}}))
resp = json.loads(ws_b.recv())
targets = resp.get('result', {}).get('targetInfos', [])
print(f"当前有 {len(targets)} 个目标", flush=True)

# 关闭所有非 summon 的页面
for t in targets:
    tid = t['targetId']
    url = t.get('url', '')
    title = t.get('title', '')[:30]
    print(f"  {title} | {url[:60]}", flush=True)
    if 'summon' not in url:
        cmd_id += 1
        ws_b.send(json.dumps({'id': cmd_id, 'method': 'Target.closeTarget', 'params': {'targetId': tid}}))
        r = json.loads(ws_b.recv())
        print(f"    关闭: {r}", flush=True)
        time.sleep(0.5)

time.sleep(2)

# 3. 创建新页面到发布页
cmd_id += 1
ws_b.send(json.dumps({'id': cmd_id, 'method': 'Target.createTarget', 'params': {
    'url': 'about:blank',
    'newWindow': False
}}))
resp = json.loads(ws_b.recv())
target_id = resp.get('result', {}).get('targetId')
print(f"\n新页面 target: {target_id}", flush=True)
ws_b.close()

if not target_id:
    print("❌ 创建页面失败", flush=True)
    exit()

# 4. 连接到新页面并导航
time.sleep(2)
page_ws_url = f'ws://localhost:9223/devtools/page/{target_id}'
ws_p = websocket.create_connection(page_ws_url, timeout=10)
ws_p.settimeout(10)

def cdp(ws, method, params=None):
    cmd_id = int(time.time() * 1000) % 100000
    ws.send(json.dumps({'id': cmd_id, 'method': method, 'params': params or {}}))
    try:
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd_id:
                if 'error' in resp:
                    return {'error': resp['error']}
                return resp.get('result')
    except:
        return None

def js(ws, expr):
    r = cdp(ws, 'Runtime.evaluate', {
        'expression': expr, 'returnByValue': True
    })
    if r and 'result' in r:
        return r['result'].get('value')
    return None

# 导航到发布页
print("导航到发布页...", flush=True)
cdp(ws_p, 'Page.navigate', {
    'url': 'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'
})
time.sleep(6)

text = js(ws_p, 'document.body.innerText')
if text and len(text) > 100:
    print(f"✅ 发布页加载, 文本长度: {len(text)}", flush=True)
    
    # 智能封面
    js(ws_p, '''
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
    
    text2 = js(ws_p, 'document.body.innerText')
    if text2 and '一键生成' in text2:
        print("✅ 智能封面弹窗出现", flush=True)
        js(ws_p, '''
        document.querySelectorAll('*').forEach(function(el) {
            if (el.textContent && el.textContent.trim() === '一键生成封面') {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.click();
            }
        });
        ''')
        time.sleep(5)
        
        text3 = js(ws_p, 'document.body.innerText')
        if text3 and '使用封面' in text3:
            print("✅ 点击使用封面", flush=True)
            js(ws_p, '''
            document.querySelectorAll('*').forEach(function(el) {
                if (el.textContent && el.textContent.trim() === '使用封面') {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.click();
                }
            });
            ''')
            time.sleep(3)
            print("✅ 封面已设置！", flush=True)
    
    # 下一步
    print("点击下一步...", flush=True)
    js(ws_p, '''
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
    
    # 检查页面
    pages = requests.get('http://localhost:9223/json').json()
    print(f"\n页面 ({len(pages)}):", flush=True)
    for p in pages:
        url = p.get('url', '')
        print(f"  {p['title'][:30]} | {url[:80]}", flush=True)
        if 'letsign' in url:
            print(f"  ✅ 合同页!", flush=True)
    
    text4 = js(ws_p, 'document.body.innerText')
    if text4:
        print(f"\n底部400字: ...{text4[-400:]}", flush=True)
        for kw in ['批量签署', '意愿认证', '获取验证码']:
            if kw in text4:
                print(f"  ✅ {kw}", flush=True)
else:
    print(f"❌ 发布页加载失败, text={text[:100] if text else 'None'}", flush=True)

ws_p.close()
print("\n✅ 完成", flush=True)
