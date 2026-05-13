"""通过 CDP websocket 检查发布页"""
import json, requests
from DrissionPage import ChromiumPage

# 快速检查是否有 dialog
resp = requests.get('http://localhost:9223/json').json()
pub = [p for p in resp if 'complete-publish' in p.get('url', '')]
if pub:
    print(f"发布页URL: {pub[0]['url'][:100]}", flush=True)
    print(f"页面标题: {pub[0]['title']}", flush=True)

# 尝试创建 ChromiumPage（带超时保护）
import threading, sys, time

result = {'done': False, 'error': None}

def create_page():
    try:
        p = ChromiumPage(addr_or_opts='127.0.0.1:9223')
        result['page'] = p
        result['done'] = True
    except Exception as e:
        result['error'] = str(e)
        result['done'] = True

t = threading.Thread(target=create_page)
t.daemon = True
t.start()
t.join(timeout=10)

if not result['done']:
    print("❌ ChromiumPage 创建超时！Chrome 可能有未处理的弹窗", flush=True)
elif result['error']:
    print(f"❌ ChromiumPage 错误: {result['error']}", flush=True)
else:
    P = result['page']
    print("✅ ChromiumPage 连接成功", flush=True)
    
    # 切换到发布页
    P.run_cdp('Target.activateTarget', targetId=pub[0]['id'])
    time.sleep(3)
    
    # 处理弹窗
    try:
        P.run_cdp('Page.handleJavaScriptDialog', accept=True)
        print("已处理弹窗", flush=True)
    except:
        pass
    
    body = P.ele('tag:body').text
    print(f"发布页文本 (len={len(body)}):", flush=True)
    print(body[:3000], flush=True)
