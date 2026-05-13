"""处理所有页面弹窗 + 导航到发布表单"""
import time, json
import websocket

CDP_WS = "ws://localhost:9223/devtools/browser/300513dd-ad24-468d-bf85-0f325ed18d21"

def cdp_cmd(ws, method, params=None, timeout=5):
    cmd_id = int(time.time() * 1000) % 100000
    msg = json.dumps({'id': cmd_id, 'method': method, 'params': params or {}})
    ws.send(msg)
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == cmd_id:
            if 'error' in resp:
                print(f"  CDP错误 {method}: {resp['error']}")
                return None
            return resp.get('result')

# 1. 获取所有页面 target
ws = websocket.create_connection(CDP_WS, timeout=10)
result = cdp_cmd(ws, 'Target.getTargets')
ws.close()

targets = result.get('targetInfos', []) if result else []
print(f"共有 {len(targets)} 个页面", flush=True)

for t in targets:
    tid = t['id']
    url = t.get('url', '')[:80]
    print(f"  页面: {t.get('title','')[:30]} | {url}", flush=True)
    
    # 连接到每个页面 dialog
    ws2 = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=5)
    try:
        dialog_info = cdp_cmd(ws2, 'Page.getJavaScriptDialogInfo')
        if dialog_info and dialog_info.get('hasDialog'):
            msg = dialog_info.get('message', '')[:50]
            print(f"    ⚠️ 有弹窗: {msg}", flush=True)
            cdp_cmd(ws2, 'Page.handleJavaScriptDialog', {'accept': True})
            print(f"    ✅ 已处理", flush=True)
        else:
            print(f"    ✅ 无弹窗", flush=True)
    except Exception as e:
        print(f"    ❌ 错误: {e}", flush=True)
    finally:
        ws2.close()

print("\n弹窗处理完成！", flush=True)
