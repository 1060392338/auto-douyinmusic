"""合同签署：切换letsign页 + 获取验证码"""
import time, json, requests, websocket

# 查找 letsign 页面
pages = requests.get('http://localhost:9223/json').json()
letsign_page = None
for p in pages:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:100]}", flush=True)
    if 'letsign' in url or 'letsign.com' in url:
        letsign_page = p
        print(f"  ✅ letsign 页!", flush=True)

if not letsign_page:
    print("❌ 没有 letsign 页面", flush=True)
    exit()

# 连接 letsign 页
ws = websocket.create_connection(letsign_page['webSocketDebuggerUrl'], timeout=10)

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

# 激活页面
cdp('Page.bringToFront')
time.sleep(3)

# 获取文本
text = js('document.body.innerText')
print(f"\nletsign 文本 (前300): {text[:300] if text else 'None'}", flush=True)

# 点击批量签署
if text and '批量签署' in text:
    print("点击批量签署...", flush=True)
    js('''
    document.querySelectorAll('button').forEach(function(b) {
        if (b.textContent.trim() === '批量签署') {
            b.scrollIntoView({behavior:'instant',block:'center'});
            b.focus();
            ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                b.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
            });
        }
    });
    ''')
    time.sleep(3)
    
    text2 = js('document.body.innerText')
    print(f"点击后文本 (前300): {text2[:300] if text2 else 'None'}", flush=True)
    
    if text2 and '获取验证码' in text2:
        print("✅ 验证码界面已出现！", flush=True)
        
        # 获取验证码元素信息
        elem = js('''
        (function() {
            var info = {getCode: null, codeInput: null, confirm: null};
            document.querySelectorAll('*').forEach(function(el) {
                var t = (el.textContent || '').trim();
                if (t === '获取验证码') {
                    info.getCode = {tag: el.tagName, cls: (el.className || '').substring(0,50), outer: el.outerHTML.substring(0,150)};
                }
                if (t === '确定') {
                    info.confirm = {tag: el.tagName, cls: (el.className || '').substring(0,50), outer: el.outerHTML.substring(0,100)};
                }
            });
            document.querySelectorAll('input').forEach(function(inp) {
                var ph = (inp.placeholder || '');
                if (ph.indexOf('验证码') >= 0 || ph.indexOf('数字') >= 0) {
                    info.codeInput = {placeholder: ph, maxlength: inp.maxLength};
                }
            });
            return JSON.stringify(info);
        })();
        ''')
        print(f"\n📝 验证码元素: {elem}", flush=True)
        
        # 先聚焦输入框再点获取验证码
        js('''
        document.querySelectorAll('input').forEach(function(inp) {
            var ph = (inp.placeholder || '');
            if (ph.indexOf('验证码') >= 0 || ph.indexOf('数字') >= 0) {
                inp.focus();
                inp.click();
            }
        });
        ''')
        time.sleep(1)
        
        # 点击获取验证码
        js('''
        document.querySelectorAll('*').forEach(function(el) {
            var t = (el.textContent || '').trim();
            if (t === '获取验证码') {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.focus();
                ['mousedown','mouseup','click'].forEach(function(ev) {
                    el.dispatchEvent(new MouseEvent(ev, {bubbles:true, cancelable:true, view:window, button:0}));
                });
            }
        });
        ''')
        print("\n✅ 获取验证码已点击！请查收手机短信")
        
        text3 = js('document.body.innerText')
        if text3 and '验证码已发送' in text3:
            print("✅ 验证码已发送至手机！")
    else:
        print("❌ 未出现验证码界面", flush=True)
        if text2:
            print(f"文本: {text2[:500]}", flush=True)
else:
    print(f"❌ 无批量签署按钮", flush=True)
    print(f"letSign全文: {text}", flush=True)

ws.close()
print("\n✅ 请把验证码发给我，我来填入并完成签署", flush=True)
