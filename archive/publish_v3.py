#!/usr/bin/env python3
"""
发布 v3 - 全CDP直连方式
"""
import sys, time, os, signal, json
import requests, websocket

def _cleanup(signum, frame):
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""

BWS = "http://localhost:9223"
print(f"=== 发布 {song} ===\n", flush=True)

def get_browser_ws():
    ver = requests.get(f'{BWS}/json/version', timeout=5).json()
    return ver['webSocketDebuggerUrl']

def cdp_page(page_ws, method, params=None):
    if params is None: params = {}
    ws = websocket.create_connection(page_ws, timeout=10)
    ws.send(json.dumps({'id':1, 'method':method, 'params':params}))
    r = json.loads(ws.recv())
    ws.close()
    return r

def cdp_target(target_id, method, params=None):
    if params is None: params = {}
    ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{target_id}', timeout=10)
    ws.send(json.dumps({'id':1, 'method':method, 'params':params}))
    r = json.loads(ws.recv())
    ws.close()
    return r

def eval_js(target_id, js_code):
    r = cdp_target(target_id, 'Runtime.evaluate', {
        'expression': js_code,
        'returnByValue': True,
        'awaitPromise': False
    })
    return r.get('result',{}).get('result',{}).get('value')

# ── 1. 从资产页取 work-id ──
bws = get_browser_ws()

# 找assets页
b_ws = websocket.create_connection(bws, timeout=5)
b_ws.send(json.dumps({'id':1, 'method':'Target.getTargets', 'params':{}}))
resp = json.loads(b_ws.recv())
b_ws.close()

assets_tid = None
for t in resp.get('result',{}).get('targetInfos',[]):
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']
        break

if not assets_tid:
    print("❌ 未找到资产页，创建一个", flush=True)
    b_ws2 = websocket.create_connection(bws, timeout=5)
    b_ws2.send(json.dumps({'id':1, 'method':'Target.createTarget', 'params':{'url':'https://music.douyin.com/studio/assets'}}))
    r = json.loads(b_ws2.recv())
    assets_tid = r.get('result',{}).get('targetId','')
    b_ws2.close()
    time.sleep(5)

# 提取 work-id
wid = eval_js(assets_tid, f"""
(function() {{
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for(var i=0; i<cards.length; i++) {{
        if(cards[i].textContent.includes('{song}')) {{
            return cards[i].getAttribute('data-work-id') || '';
        }}
    }}
    return '';
}})();
""")

if not wid:
    print(f"❌ 未找到歌曲 {song} 的work-id", flush=True)
    sys.exit(1)
print(f"work-id: {wid}", flush=True)

# ── 2. 清理旧的complete-publish页，创建新页 ──
b_ws3 = websocket.create_connection(bws, timeout=5)
b_ws3.send(json.dumps({'id':1, 'method':'Target.getTargets', 'params':{}}))
resp3 = json.loads(b_ws3.recv())
for t in resp3.get('result',{}).get('targetInfos',[]):
    if 'complete-publish' in t.get('url','') and t['type'] == 'page':
        b_ws3.send(json.dumps({'id':2, 'method':'Target.closeTarget', 'params':{'targetId':t['targetId']}}))
        json.loads(b_ws3.recv())
        print("  清理旧发布页✅", flush=True)
b_ws3.close()

b_ws4 = websocket.create_connection(bws, timeout=5)
b_ws4.send(json.dumps({'id':1, 'method':'Target.createTarget', 'params':{'url':'about:blank'}}))
r4 = json.loads(b_ws4.recv())
pub_tid = r4.get('result',{}).get('targetId','')
b_ws4.close()

pub_url = f"https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId={wid}"
print(f"URL: {pub_url[:80]}", flush=True)

# 导航
cdp_target(pub_tid, 'Page.enable')
cdp_target(pub_tid, 'Page.navigate', {'url': pub_url})
time.sleep(5)
eval_js(pub_tid, "window.onbeforeunload=null;")
print("1. 进入发布页✅", flush=True)
time.sleep(2)

# ── 3. 智能封面 ──
print("2. 智能封面...", flush=True)
eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '智能封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(3)

eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(4)

eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '使用封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return 'used';
        }
    }
    return 'not-found';
})();
""")
time.sleep(2)
print("   封面✅", flush=True)

# 检查页面文本长度
text_len = eval_js(pub_tid, "document.body.textContent.length")
print(f"   文本长度(后): {text_len}", flush=True)

# ── 4. 第一次下一步 ──
print("3. 第一次下一步...", flush=True)
eval_js(pub_tid, "window.scrollTo(0, document.body.scrollHeight);")
time.sleep(1)

eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('button');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent.trim() === '下一步') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            ['mousedown','mouseup','click'].forEach(function(t) {
                all[i].dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window, button:0}));
            });
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(4)

text_len2 = eval_js(pub_tid, "document.body.textContent.length")
print(f"   文本长度: {text_len2}", flush=True)

# ── 5. 艺人信息 ──
print("4. 艺人信息...", flush=True)
eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '有主页链接') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(2)

eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '无主页链接') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(1)
print("   艺人信息✅", flush=True)

# ── 6. 第二次下一步 ──
print("5. 第二次下一步...", flush=True)
eval_js(pub_tid, """
(function() {
    var all = document.querySelectorAll('button');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent.trim() === '下一步') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            ['mousedown','mouseup','click'].forEach(function(t) {
                all[i].dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window, button:0}));
            });
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(5)

# ── 7. 找letsign ──
print("6. 找letsign...", flush=True)
b_ws5 = websocket.create_connection(bws, timeout=5)
b_ws5.send(json.dumps({'id':1, 'method':'Target.getTargets', 'params':{}}))
resp5 = json.loads(b_ws5.recv())
b_ws5.close()

letsign_tid = None
letsign_url = ""
for t in resp5.get('result',{}).get('targetInfos',[]):
    url = t.get('url','')
    if 'letsign' in url and t['type'] == 'page':
        letsign_tid = t['targetId']
        letsign_url = url
        break

if letsign_tid:
    print(f"✅ letsign: {letsign_url[:60]}...", flush=True)
    
    # 点批量签署
    eval_js(letsign_tid, """
    (function() {
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++) {
            if(btns[i].textContent.trim() === '批量签署') {
                btns[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    """)
    time.sleep(3)
    
    # 检查验证码区域
    l_text = eval_js(letsign_tid, "document.body.textContent.substring(0, 1000)")
    print(f"   letsign文本: {l_text[:100]}", flush=True)
    
    if verify_code:
        # 填入验证码
        eval_js(letsign_tid, f"""
        (function() {{
            var inputs = document.querySelectorAll('input');
            for(var i=0; i<inputs.length; i++) {{
                var ph = inputs[i].placeholder || '';
                if(ph.includes('验证码') || ph.includes('数字')) {{
                    inputs[i].focus();
                    var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    s.call(inputs[i], '{verify_code}');
                    inputs[i].dispatchEvent(new Event('input', {{bubbles:true}}));
                    inputs[i].dispatchEvent(new Event('change', {{bubbles:true}}));
                    return 'filled';
                }}
            }}
            return 'no-input';
        }})();
        """)
        time.sleep(1)
        
        # 点确定
        eval_js(letsign_tid, """
        (function() {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '确定') {
                    all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                    return 'confirmed';
                }
            }
            return 'not-found';
        })();
        """)
        time.sleep(4)
        
        signed = eval_js(letsign_tid, "document.body.textContent.includes('签署成功')")
        if signed:
            print("✅ 签署成功！", flush=True)
        else:
            final_t = eval_js(letsign_tid, "document.body.textContent.substring(0, 500)")
            print(f"签署状态: {final_t[:100]}", flush=True)
    else:
        # 先聚焦输入框再点获取验证码
        eval_js(letsign_tid, """
        (function() {
            var inputs = document.querySelectorAll('input');
            for(var i=0; i<inputs.length; i++) {
                var ph = inputs[i].placeholder || '';
                if(ph.includes('验证码') || ph.includes('数字')) {
                    inputs[i].focus();
                    inputs[i].click();
                    return 'focused: ' + ph;
                }
            }
            return 'no-input';
        })();
        """)
        time.sleep(1)
        
        eval_js(letsign_tid, """
        (function() {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                var t = all[i].textContent;
                if(t && t.trim() === '获取验证码') {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                    return 'clicked';
                }
            }
            return 'not-found';
        })();
        """)
        print("   验证码已发送！", flush=True)
        # 保存状态
        with open('/tmp/publish_state.json', 'w') as f:
            json.dump({'song': song, 'letsign_tid': letsign_tid, 'wid': wid}, f)
        print(f"\n>>> 陛下，请查看手机验证码，然后告诉我 <<<", flush=True)
else:
    print("❌ 未找到letsign标签页", flush=True)
    # 检查发布页当前状态
    cur_text = eval_js(pub_tid, "document.body.textContent.substring(0, 500)")
    print(f"发布页现状: {cur_text[:200]}", flush=True)

print(f"\n=== 发布 {song} 阶段完成 ===", flush=True)
