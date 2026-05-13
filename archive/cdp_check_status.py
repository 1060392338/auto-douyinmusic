"""CDP 检查资产页"""
import time, json, requests, websocket

# 关闭旧发布页
bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)
for p in requests.get('http://localhost:9223/json').json():
    if 'complete-publish' in p.get('url',''):
        b.send(json.dumps({'id':1, 'method':'Target.closeTarget', 'params':{'targetId':p['id']}}))
        json.loads(b.recv())
        time.sleep(1)
b.close()
time.sleep(2)

# 新页面
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

text = js('document.body.innerText')
print(f"✅ 资产页, 文本:{len(text) if text else '?'}", flush=True)

if text:
    # 检查蝉声漫旧夏
    if '蝉声漫旧夏' in text:
        idx = text.find('蝉声漫旧夏')
        print(f"\n蝉声漫旧夏上下文:", flush=True)
        print(f"...{text[max(0,idx-50):idx+200]}...", flush=True)
    
    # 状态
    for kw in ['已发行','发行成功','已发布','审核中','审核通过','发行全曲','已提交','处理中']:
        if kw in text:
            print(f"✅ {kw}", flush=True)
    
    # 所有歌曲
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if 2 <= len(line) <= 8 and line not in ['首页','素材','我的资产','自由创作','收藏','作品','批量操作','工程文件','知识库']:
            if not line.startswith(('0','1','2','3','4','5','6','7','8','9')):
                next_lines = [lines[j].strip() for j in range(i+1, min(i+4, len(lines))) if lines[j].strip()]
                print(f"\n{line}: {' | '.join(next_lines)}", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
