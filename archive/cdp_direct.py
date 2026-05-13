"""使用 CDP websocket 直接操作发布流程"""
import time, json, requests, websocket

def cdp_call(ws, method, params=None):
    """发送 CDP 命令并等待返回"""
    cmd_id = int(time.time() * 1000) % 100000
    ws.send(json.dumps({'id': cmd_id, 'method': method, 'params': params or {}}))
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == cmd_id:
            if 'error' in resp:
                print(f"  ❌ CDP错误 {method}: {resp['error']}", flush=True)
                return None
            return resp.get('result')

def js_eval(ws, js):
    """执行 JS 并返回值"""
    result = cdp_call(ws, 'Runtime.evaluate', {
        'expression': js,
        'returnByValue': True,
        'awaitPromise': True
    })
    if result:
        val = result.get('result', {}).get('value', '')
        return val
    return None

# 获取发布页 WS URL
pages = requests.get('http://localhost:9223/json').json()
pub = [p for p in pages if 'complete-publish' in p.get('url', '')]
if not pub:
    print("❌ 无发布页", flush=True)
    exit()

ws_url = pub[0]['webSocketDebuggerUrl']
print(f"连接发布页: {ws_url[:60]}...", flush=True)

ws = websocket.create_connection(ws_url, timeout=10)

# 激活页面
cdp_call(ws, 'Page.bringToFront')
time.sleep(1)

# 处理弹窗
diag = cdp_call(ws, 'Page.getJavaScriptDialogInfo')
if diag and diag.get('hasDialog'):
    cdp_call(ws, 'Page.handleJavaScriptDialog', {'accept': True})
    print("✅ 已处理弹窗", flush=True)

# 获取页面文本
text = js_eval(ws, 'document.body.innerText')
print(f"页面文本长度: {len(text) if text else '?'}", flush=True)
if text:
    print(f"底部600字: ...{text[-600:]}", flush=True)

# 搜索关键文本
if text:
    for kw in ['批量签署', '意愿认证', '获取验证码', '合同签署', 'letsign', 
               '授权信息', '授权比例', '签约', '下一步', '上一步', '签署协议（1）']:
        if kw in text:
            print(f"✅ 找到: {kw}", flush=True)

# 滚动到底部
js_eval(ws, 'window.scrollTo(0, document.body.scrollHeight);')
time.sleep(2)

# 再次获取文本
text2 = js_eval(ws, 'document.body.innerText')
if text2 and text2 != text:
    print(f"\n滚动后文本不同! 新底部300字: ...{text2[-300:]}", flush=True)
    for kw in ['批量签署', '意愿认证', '获取验证码', '合同签署', 'letsign']:
        if kw in text2:
            print(f"✅ 滚动后找到: {kw}", flush=True)

ws.close()
print("\n✅ 检查完成", flush=True)
