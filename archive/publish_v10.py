#!/usr/bin/env python3
"""
发布 v10 - 完整端到端发布脚本
用法: python3 publish_v10.py <歌名> [验证码]
"""
import sys, time, json, requests, os, signal
from DrissionPage import ChromiumPage

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
code = sys.argv[2] if len(sys.argv) > 2 else ""

def _cleanup(signum, frame):
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

BWS = 'http://localhost:9223'
def cdp(method, params=None):
    if params is None: params = {}
    import websocket
    ver = requests.get(f'{BWS}/json/version', timeout=5).json()
    ws = websocket.create_connection(ver['webSocketDebuggerUrl'], timeout=5)
    ws.send(json.dumps({'id':1,'method':method,'params':params}))
    r = json.loads(ws.recv())
    ws.close()
    return r

def eval_t(tid, js):
    import websocket
    w = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
    r = json.loads(w.recv())
    w.close()
    v = r.get('result',{}).get('result',{}).get('value')
    return v if v is not None else ''

print(f"=== 发布 {song} ===\n", flush=True)

# 1. 清理 + 资产页点发行全曲
targets = cdp('Target.getTargets').get('result',{}).get('targetInfos',[])
for t in targets:
    if 'complete-publish' in t.get('url',''):
        cdp('Target.closeTarget', {'targetId':t['targetId']})

assets_tid = None
for t in targets:
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']
        break

if not assets_tid:
    print("❌ 资产页未找到")
    sys.exit(1)

eval_t(assets_tid, f'''
(function() {{
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for(var i=0; i<cards.length; i++) {{
        if(cards[i].textContent.includes("{song}")) {{
            var all = cards[i].querySelectorAll('*');
            for(var j=0; j<all.length; j++) {{
                if(all[j].textContent && all[j].textContent.trim() === "发行全曲") {{
                    all[j].scrollIntoView({{behavior:"instant", block:"center"}});
                    ["pointerdown","pointerup","click"].forEach(function(t) {{
                        all[j].dispatchEvent(new PointerEvent(t, {{bubbles:true, cancelable:true}}));
                    }});
                    return;
                }}
            }}
        }}
    }}
}})();
''')
print("1. 点击发行全曲✅", flush=True)
time.sleep(5)

# 2. 找发布页
targets2 = cdp('Target.getTargets').get('result',{}).get('targetInfos',[])
pub_tid = None
for t in targets2:
    if 'complete-publish' in t.get('url','') and t['type'] == 'page':
        pub_tid = t['targetId']
        break

if not pub_tid:
    print("❌ 发布页未生成")
    sys.exit(1)

# 3. 用DrissionPage操作
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
tabs = P.get_tabs()
for tab in tabs:
    if 'complete-publish' in tab.url:
        P = tab
        break
time.sleep(2)
P.run_js("window.onbeforeunload=null")
print("2. 进入发布页✅", flush=True)

# 4. Step1 - 点下一步
try:
    next_btn = P.ele('xpath://button[contains(.,"下一步")]', timeout=5)
    next_btn.click()
    print("3. 下一步1✅", flush=True)
except:
    print("  无下一步按钮", flush=True)
time.sleep(4)

# 5. Step2 - 处理表演者+艺人信息
for i in range(3):
    try:
        add_btn = P.ele('xpath://button[contains(.,"添加自己")]', timeout=3)
        if add_btn and add_btn.offsetWidth > 0:
            add_btn.click()
            time.sleep(2)
    except:
        pass
# 艺人信息
for txt in ['有主页链接', '无主页链接']:
    try:
        el = P.ele(f'xpath://*[contains(text(),"{txt}")]', timeout=3)
        if el:
            el.click()
            time.sleep(1)
    except:
        pass
print("4. 表演者/艺人✅", flush=True)

# 6. 点下一步2
try:
    next2 = P.ele('xpath://button[contains(.,"下一步")]', timeout=5)
    next2.click()
    print("5. 下一步2✅", flush=True)
except:
    print("  无下一步2", flush=True)
time.sleep(5)

# 7. 找letsign
targets3 = cdp('Target.getTargets').get('result',{}).get('targetInfos',[])
letsign_tid = None
for t in targets3:
    if 'letsign' in t.get('url',''):
        letsign_tid = t['targetId']
        print(f"6. letsign✅", flush=True)
        break

if letsign_tid:
    # 点批量签署
    eval_t(letsign_tid, '''
    (function() {
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++) {
            if(btns[i].textContent.trim() === '批量签署') {
                btns[i].dispatchEvent(new PointerEvent('click', {bubbles:true, cancelable:true}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''')
    time.sleep(3)
    
    # 聚焦+发送验证码
    eval_t(letsign_tid, '''
    (function() {
        var inputs = document.querySelectorAll('input');
        for(var i=0; i<inputs.length; i++) {
            if(inputs[i].placeholder && inputs[i].placeholder.includes('数字')) {
                inputs[i].focus();
                inputs[i].click();
                return 'focused';
            }
        }
        return 'no-input';
    })();
    ''')
    time.sleep(1)
    
    eval_t(letsign_tid, '''
    (function() {
        var el = document.querySelector('.ds-captcha-next__form-send');
        if(el) {
            el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
        return 'not-found';
    })();
    ''')
    print("   验证码已发送!", flush=True)
    
    if code:
        # 填入验证码
        eval_t(letsign_tid, f'''
        (function() {{
            var inputs = document.querySelectorAll('input');
            for(var i=0; i<inputs.length; i++) {{
                if(inputs[i].placeholder && inputs[i].placeholder.includes('数字')) {{
                    var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    s.call(inputs[i], '{code}');
                    inputs[i].dispatchEvent(new Event('input', {{bubbles:true}}));
                    inputs[i].dispatchEvent(new Event('change', {{bubbles:true}}));
                    return 'filled';
                }}
            }}
            return 'no-input';
        }})();
        ''')
        time.sleep(1)
        
        # 点确定
        eval_t(letsign_tid, '''
        (function() {
            var btns = document.querySelectorAll('button.letsign-btn');
            for(var i=0; i<btns.length; i++) {
                if(btns[i].textContent.trim() === '确定') {
                    btns[i].click();
                    ['mousedown','mouseup','click'].forEach(function(t) {
                        btns[i].dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window, button:0}));
                    });
                    return 'confirmed';
                }
            }
            return 'not-found';
        })();
        ''')
        time.sleep(5)
        
        result = eval_t(letsign_tid, 'document.body.textContent')
        if '签署成功' in result:
            print("7. ✅ 签署成功！等待跳转...", flush=True)
            # 等待自动跳转
            time.sleep(5)
            
            # 回到资产页验证
            try:
                P.run_js("window.onbeforeunload=null")
                P.run_js("window.location.href='https://music.douyin.com/studio/assets'")
                time.sleep(6)
                body = P.ele('tag:body').text
                idx = body.find(song)
                if idx >= 0:
                    snippet = body[idx:idx+60]
                    if '查看详情' in snippet:
                        print(f"✅ {song} 发布成功！", flush=True)
                    else:
                        print(f"⚠️ 状态: {snippet[:40]}", flush=True)
                else:
                    print(f"⚠️ 未找到{song}", flush=True)
            except Exception as e:
                print(f"验证异常: {e}", flush=True)
        elif '验证码错误' in result:
            print("❌ 验证码错误，请重试", flush=True)
            with open('/tmp/pub_state.json', 'w') as f:
                json.dump({'song': song, 'letsign_tid': letsign_tid}, f)
        else:
            print(f"签署状态: ...", flush=True)
    else:
        print(f"\n>>> 陛下，请查看手机验证码 {song} <<<", flush=True)
        with open('/tmp/pub_state.json', 'w') as f:
            json.dump({'song': song, 'letsign_tid': letsign_tid}, f)
else:
    print("❌ 无letsign", flush=True)

print(f"\n=== {song} 完成 ===", flush=True)
