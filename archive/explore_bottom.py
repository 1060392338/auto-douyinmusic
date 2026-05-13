"""继续：在授权页面滚动+找签署入口"""
import time, json, requests, websocket

bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)

# 关闭旧发布页
for p in requests.get('http://localhost:9223/json').json():
    url = p.get('url','')
    if 'console/complete-publish' in url:
        cid = 1
        b.send(json.dumps({'id':cid, 'method':'Target.closeTarget', 'params':{'targetId': p['id']}}))
        json.loads(b.recv())
        print(f"关闭旧页: {p['id'][:20]}", flush=True)
        time.sleep(1)

b.close()
time.sleep(2)

# 创建新页面
b2 = websocket.create_connection(requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl'], timeout=5)
b2.send(json.dumps({'id':1, 'method':'Target.createTarget', 'params':{'url':'about:blank'}}))
r = json.loads(b2.recv())
b2.close()
tid = r.get('result',{}).get('targetId')
if not tid:
    print("❌ 创建失败", flush=True)
    exit()

ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)

def cdp(method, params=None, timeout=5):
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

def js(expr):
    r = cdp('Runtime.evaluate', {'expression':expr, 'returnByValue':True})
    return r.get('result',{}).get('value') if r else None

# 导航
cdp('Page.navigate', {'url':'https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379'})
time.sleep(8)
cdp('Page.handleJavaScriptDialog', {'accept':True})
js('window.onbeforeunload=null;')

text = js('document.body.innerText')
print(f"✅ 发布页, 文本长度:{len(text)}", flush=True)

# 如果有智能封面弹窗关掉
if text and '使用封面' in text:
    js('''
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if ((t === '取消' || t === '关闭') && el.offsetParent !== null) {
            el.click();
        }
    });
    ''')
    time.sleep(2)

# 先滚动到底部看全貌
js('window.scrollTo(0, 0);')
time.sleep(1)

# 分次滚动并检查
for i in range(8):
    js(f'window.scrollTo(0, {i * 500});')
    time.sleep(1)
    t = js('document.body.innerText')
    if t:
        print(f"  滚动 {i*500}px: 文本长度={len(t)}", flush=True)

# 最终底部
js('window.scrollTo(0, document.body.scrollHeight);')
time.sleep(3)

full_text = js('document.body.innerText')
print(f"\n最终文本长度: {len(full_text) if full_text else '?'}", flush=True)
if full_text:
    print(f"底部800字:", flush=True)
    print(full_text[-800:], flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','签署','同意','下一步','上一步']:
        if kw in full_text:
            print(f"  ✅ {kw}", flush=True)

# 检查所有页面
pages = requests.get('http://localhost:9223/json').json()
print(f"\n页面:", flush=True)
for p in pages:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:100]}", flush=True)
    if 'letsign' in url:
        print(f"  ✅ 合同页!", flush=True)

# 用 JS 检查 DOM 结构
elem_info = js('''
(function() {
    var info = {buttons: [], inputs: [], iframes: []};
    document.querySelectorAll('button').forEach(function(b) {
        var t = (b.textContent || '').trim();
        if (t) info.buttons.push({text: t, visible: b.offsetParent !== null, tag: 'button'});
    });
    document.querySelectorAll('div[class*="next"], div[class*="Next"], div[class*="submit"], div[class*="Submit"]').forEach(function(d) {
        var t = (d.textContent || '').trim();
        if (t) info.buttons.push({text: t.substring(0,30), visible: d.offsetParent !== null, tag: 'div'});
    });
    document.querySelectorAll('iframe').forEach(function(f) {
        info.iframes.push({src: (f.src || '').substring(0,100)});
    });
    document.querySelectorAll('input').forEach(function(inp) {
        var ph = (inp.placeholder || '');
        if (ph) info.inputs.push({placeholder: ph.substring(0,30)});
    });
    return JSON.stringify(info);
})();
''')
print(f"\nDOM 结构:", flush=True)
print(elem_info, flush=True)

ws.close()
print("\n✅ 完成", flush=True)
