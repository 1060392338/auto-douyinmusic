"""动态获取浏览器WS并处理所有弹窗"""
import time, json, requests
import websocket

# 获取 browser WS URL
ver = requests.get('http://localhost:9223/json/version').json()
CDP_WS = ver['webSocketDebuggerUrl']
print(f"Browser WS: {CDP_WS}", flush=True)

def cdp_cmd(ws, method, params=None):
    cmd_id = int(time.time() * 1000) % 100000
    msg = json.dumps({'id': cmd_id, 'method': method, 'params': params or {}})
    ws.send(msg)
    timeout = 5
    start = time.time()
    while time.time() - start < timeout:
        resp = json.loads(ws.recv())
        if resp.get('id') == cmd_id:
            if 'error' in resp:
                return None
            return resp.get('result')
    return None

# 获取所有 target
ws = websocket.create_connection(CDP_WS, timeout=5)
result = cdp_cmd(ws, 'Target.getTargets')
ws.close()

targets = result.get('targetInfos', []) if result else []
print(f"共有 {len(targets)} 个页面", flush=True)

for t in targets:
    tid = t['id']
    url = t.get('url', '')[:80]
    title = t.get('title', '')[:30]
    print(f"  页面: {title} | {url}", flush=True)
    
    ws2 = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=5)
    try:
        dialog_info = cdp_cmd(ws2, 'Page.getJavaScriptDialogInfo')
        if dialog_info and dialog_info.get('hasDialog'):
            msg = dialog_info.get('message', '')[:80]
            print(f"    ⚠️ 有弹窗: {msg}", flush=True)
            cdp_cmd(ws2, 'Page.handleJavaScriptDialog', {'accept': True})
            print(f"    ✅ 已处理", flush=True)
        else:
            print(f"    ✅ 无弹窗", flush=True)
    except Exception as e:
        print(f"    ❌ 错误: {e}", flush=True)
    finally:
        ws2.close()

print("\n✅ 弹窗处理完成！", flush=True)
