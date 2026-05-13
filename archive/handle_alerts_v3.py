"""使用 /json 接口获取页面并处理弹窗"""
import time, json, requests
import websocket

# 获取所有页面
pages = requests.get('http://localhost:9223/json').json()
print(f"共有 {len(pages)} 个页面", flush=True)

for p in pages:
    ws_url = p['webSocketDebuggerUrl']
    url = p.get('url', '')[:80]
    title = p.get('title', '')[:30]
    print(f"  页面: {title} | {url}", flush=True)
    
    try:
        ws = websocket.create_connection(ws_url, timeout=5)
        
        # 检查 dialog
        cmd_id = 1
        ws.send(json.dumps({'id': cmd_id, 'method': 'Page.getJavaScriptDialogInfo', 'params': {}}))
        resp = json.loads(ws.recv())
        
        if resp.get('result', {}).get('hasDialog'):
            msg = resp['result'].get('message', '')[:80]
            print(f"    ⚠️ 有弹窗: {msg}", flush=True)
            
            # 接受弹窗
            ws.send(json.dumps({'id': 2, 'method': 'Page.handleJavaScriptDialog', 'params': {'accept': True}}))
            r = json.loads(ws.recv())
            print(f"    ✅ 已处理: {r}", flush=True)
        else:
            print(f"    ✅ 无弹窗", flush=True)
        
        ws.close()
    except Exception as e:
        print(f"    ❌ 错误: {e}", flush=True)

print("\n✅ 全部处理完成！", flush=True)
