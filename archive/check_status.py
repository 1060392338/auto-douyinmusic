"""检查发布状态"""
import time, json, requests, websocket
from DrissionPage import ChromiumPage

# 先用 CDP 清理弹窗
pages = requests.get('http://localhost:9223/json').json()
for p in pages:
    try:
        ws = websocket.create_connection(p['webSocketDebuggerUrl'], timeout=3)
        ws.settimeout(2)
        ws.send(json.dumps({'id':1, 'method':'Page.getJavaScriptDialogInfo', 'params':{}}))
        r = json.loads(ws.recv())
        if r.get('result',{}).get('hasDialog'):
            ws.send(json.dumps({'id':2, 'method':'Page.handleJavaScriptDialog', 'params':{'accept':True}}))
            json.loads(ws.recv())
        ws.send(json.dumps({'id':3, 'method':'Runtime.evaluate', 'params':{
            'expression': 'window.onbeforeunload = null;', 'returnByValue': True
        }}))
        json.loads(ws.recv())
        ws.close()
    except:
        pass

time.sleep(2)

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
P.run_js("window.onbeforeunload=null;")

# 导航到资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(8)

body = None
for _ in range(5):
    time.sleep(2)
    try:
        body = P.ele('tag:body', timeout=5)
        if body and len(body.text) > 100:
            break
    except:
        P.run_js("window.onbeforeunload=null;")

if not body:
    print("❌ 资产页加载失败", flush=True)
    exit()

text = body.text
print(f"✅ 资产页, 文本长度:{len(text)}", flush=True)

# 搜索蝉声漫旧夏
if '蝉声漫旧夏' in text:
    idx = text.find('蝉声漫旧夏')
    start = max(0, idx-50)
    end = min(len(text), idx+200)
    print(f"\n蝉声漫旧夏上下文:", flush=True)
    print(f"...{text[start:end]}...", flush=True)

# 检查发布状态
print("\n状态检查:", flush=True)
for kw in ['已发行', '发行成功', '已发布', '审核中', '审核通过', '发行全曲', '已提交', '处理中']:
    if kw in text:
        # 找蝉声漫旧夏附近的
        if '蝉声漫旧夏' in text:
            idx = text.find('蝉声漫旧夏')
            nearby = text[idx:idx+300]
            if kw in nearby:
                print(f"  ✅ {kw} (附近)", flush=True)
            else:
                print(f"  ✅ {kw} (其他位置)", flush=True)
        else:
            print(f"  ✅ {kw}", flush=True)

# 列出所有歌曲
lines = text.split('\n')
for i, line in enumerate(lines):
    line = line.strip()
    if 2 <= len(line) <= 8 and line not in ['首页','素材','我的资产','自由创作','知识库','收藏','作品','批量操作','工程文件']:
        if not line.startswith(('0','1','2','3','4','5','6','7','8','9')):
            next_lines = lines[i+1:i+4]
            print(f"\n{line}:")
            for nl in next_lines:
                nl = nl.strip()
                if nl:
                    print(f"  -> {nl}")

print("\n✅ 检查完成", flush=True)
