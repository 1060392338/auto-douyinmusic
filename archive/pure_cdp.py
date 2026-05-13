"""纯 CDP 方案：关掉旧页面 → 新页面 → 完整发布"""
import time, json, requests, websocket

def cdp(ws, method, params=None, timeout=5):
    cid = int(time.time()*1000)%100000
    ws.send(json.dumps({'id':cid, 'method':method, 'params':params or {}}))
    ws.settimeout(timeout)
    while True:
        try:
            r = json.loads(ws.recv())
            if r.get('id')==cid:
                return r.get('result') if 'result' in r else None
        except:
            return None

def js(ws, expr):
    r = cdp(ws, 'Runtime.evaluate', {'expression':expr, 'returnByValue':True})
    return r.get('result',{}).get('value') if r else None

# 1. 获取 browser WS
bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)

# 2. 关闭所有有弹窗的页面，保留 summon
pages = requests.get('http://localhost:9223/json').json()
for p in pages:
    url = p.get('url','')
    if 'letsign' in url or ('console/complete-publish' in url):
        print(f"关闭: {p['title'][:30]}", flush=True)
        cdp(b, 'Target.closeTarget', {'targetId': p['id']})
        time.sleep(0.5)

b.close()
time.sleep(3)

# 3. 重新获取 page list 看看是否还有页面
pages = requests.get('http://localhost:9223/json').json()
print(f"剩余页面: {len(pages)}", flush=True)

# 4. 用 browser WS 创建新页面
b2 = websocket.create_connection(requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl'], timeout=5)
r = cdp(b2, 'Target.createTarget', {'url': 'about:blank'})
b2.close()

tid = r.get('targetId') if r else None
if not tid:
    print("❌ 创建页面失败", flush=True)
    exit()

print(f"新页面 target: {tid[:20]}...", flush=True)

# 5. 连接新页面
time.sleep(2)
ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
ws.settimeout(10)

# 6. 导航到发布页
print("导航到发布页...", flush=True)
cdp(ws, 'Page.navigate', {'url':'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'})
time.sleep(8)

# 处理弹窗
cdp(ws, 'Page.handleJavaScriptDialog', {'accept':True})
# 禁用弹窗
js(ws, 'window.onbeforeunload = null;')

text = js(ws, 'document.body.innerText')
if not text or len(text) < 200:
    print("❌ 加载失败", flush=True)
    ws.close()
    exit()

print(f"✅ 发布页, 文本长度:{len(text)}", flush=True)

# 7. 智能封面
print("智能封面...", flush=True)
js(ws, '''
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '智能封面') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(3)

t2 = js(ws, 'document.body.innerText')
if t2 and '一键生成' in t2:
    print("一键生成封面...", flush=True)
    js(ws, '''
    document.querySelectorAll('*').forEach(function(el) {
        if (el.textContent && el.textContent.trim() === '一键生成封面') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.click();
        }
    });
    ''')
    time.sleep(5)
    
    t3 = js(ws, 'document.body.innerText')
    if t3 and '使用封面' in t3:
        print("使用封面...", flush=True)
        js(ws, '''
        document.querySelectorAll('*').forEach(function(el) {
            if (el.textContent && el.textContent.trim() === '使用封面') {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.click();
            }
        });
        ''')
        time.sleep(3)
        
        # 如果弹窗还在，点取消
        t3b = js(ws, 'document.body.innerText')
        if t3b and '使用封面' in t3b:
            print("弹窗未关，取消...", flush=True)
            js(ws, '''
            document.querySelectorAll('*').forEach(function(el) {
                var t = (el.textContent || '').trim();
                if ((t === '取消' || t === '关闭') && el.offsetParent !== null) {
                    el.click();
                }
            });
            ''')
            time.sleep(3)

# 8. 艺人信息
t4 = js(ws, 'document.body.innerText')
if t4 and '有主页链接' in t4:
    print("艺人信息: 有主页链接→无主页链接", flush=True)
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

# 9. 滚动+下一步
print("点击下一步...", flush=True)
js(ws, 'window.onbeforeunload=null;window.scrollTo(0, document.body.scrollHeight);')
time.sleep(2)
js(ws, '''
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '下一步' && el.offsetParent !== null) {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
''')
time.sleep(8)

# 10. 检查
pages = requests.get('http://localhost:9223/json').json()
print(f"\n页面 ({len(pages)}):", flush=True)
for p in pages:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:100]}", flush=True)
    if 'letsign' in url:
        print(f"  ✅ 合同页! WS:{p['webSocketDebuggerUrl'][:60]}", flush=True)

t5 = js(ws, 'document.body.innerText')
if t5:
    print(f"\n底部600: ...{t5[-600:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','letsign']:
        if kw in t5:
            print(f"  ✅ {kw}", flush=True)

ws.close()
print("\n✅ 完成", flush=True)
