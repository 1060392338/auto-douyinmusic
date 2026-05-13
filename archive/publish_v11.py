#!/usr/bin/env python3
"""
发布 v11 - 陛下指导的完整流程
用法: python3 publish_v11.py <歌名> [验证码]
"""
import sys, time, json, requests, os, signal
from DrissionPage import ChromiumPage

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
code = sys.argv[2] if len(sys.argv) > 2 else ""

def cleanup(s, f): os._exit(0)
signal.signal(signal.SIGTERM, cleanup)
signal.signal(signal.SIGINT, cleanup)

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

# 1. 清理旧发布页 + 点发行全曲
for t in cdp('Target.getTargets').get('result',{}).get('targetInfos',[]):
    if 'complete-publish' in t.get('url',''):
        cdp('Target.closeTarget', {'targetId':t['targetId']})

assets_tid = None
for t in cdp('Target.getTargets').get('result',{}).get('targetInfos',[]):
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']; break

if not assets_tid:
    print("❌ 资产页未找到"); sys.exit(1)

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
print("1. 发行全曲✅", flush=True)
time.sleep(5)

# 2. 找发布页
pub_tid = None
for t in cdp('Target.getTargets').get('result',{}).get('targetInfos',[]):
    if 'complete-publish' in t.get('url','') and t['type'] == 'page':
        pub_tid = t['targetId']; break

if not pub_tid:
    print("❌ 发布页未生成"); sys.exit(1)

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
for tab in P.get_tabs():
    if 'complete-publish' in tab.url:
        P = tab; break
time.sleep(2)
P.run_js("window.onbeforeunload=null")

# 3. 下一步1 → 自动到Step2
try:
    P.ele('xpath://button[contains(.,"下一步")]', timeout=5).click()
    print("2. 下一步→Step2✅", flush=True)
except:
    print("   无下一步按钮", flush=True)
time.sleep(4)

# 4. Step2: 艺人信息 有主页链接→无主页链接
for txt in ['有主页链接', '无主页链接']:
    try:
        el = P.ele(f'xpath://*[contains(text(),"{txt}")]', timeout=3)
        if el: el.click(); time.sleep(1)
    except:
        pass
print("3. 艺人信息✅", flush=True)

# 5. 下一步2 → 自动到Step3
try:
    P.ele('xpath://button[contains(.,"下一步")]', timeout=5).click()
    print("4. 下一步→Step3✅", flush=True)
except:
    print("   无下一步", flush=True)
time.sleep(5)

# 6. 找letsign或提交按钮
targets = cdp('Target.getTargets').get('result',{}).get('targetInfos',[])
letsign_tid = None
for t in targets:
    if 'letsign' in t.get('url',''):
        letsign_tid = t['targetId']
        break

if letsign_tid:
    print("5. letsign✅", flush=True)
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
    
    # 聚焦+发验证码
    eval_t(letsign_tid, '''
    (function() {
        var inputs = document.querySelectorAll('input');
        for(var i=0; i<inputs.length; i++) {
            if(inputs[i].placeholder && inputs[i].placeholder.includes('数字')) {
                inputs[i].focus(); inputs[i].click(); return 'focused';
            }
        }
        return 'no-input';
    })();
    ''')
    time.sleep(1)
    
    eval_t(letsign_tid, '''
    (function() {
        var el = document.querySelector('.ds-captcha-next__form-send');
        if(el) { el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0})); return 'clicked'; }
        return 'not-found';
    })();
    ''')
    print("   验证码已发送!", flush=True)
    
    if code:
        eval_t(letsign_tid, f'''
        (function() {{
            var inputs = document.querySelectorAll('input');
            for(var i=0; i<inputs.length; i++) {{
                if(inputs[i].placeholder && inputs[i].placeholder.includes('数字')) {{
                    var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    s.call(inputs[i], '{code}');
                    inputs[i].dispatchEvent(new Event('input', {{bubbles:true}}));
                    var btns = document.querySelectorAll('button.letsign-btn');
                    for(var j=0; j<btns.length; j++) {{
                        if(btns[j].textContent.trim() === '确定') {{
                            btns[j].dispatchEvent(new MouseEvent('click', {{bubbles:true, view:window, button:0}}));
                        }}
                    }}
                    return 'done';
                }}
            }}
            return 'no-input';
        }})();
        ''')
        time.sleep(5)
        result = eval_t(letsign_tid, 'document.body.textContent.includes("签署成功")')
        print(f"   签署: {'✅成功' if result else '❌失败'}", flush=True)
    else:
        with open('/tmp/pub_state.json', 'w') as f:
            json.dump({'song': song, 'letsign_tid': letsign_tid}, f)
        print(f"\n>>> 陛下，请查看手机验证码 ({song}) <<<", flush=True)
else:
    # 没有letsign → 点"提交"
    print("5. 无letsign, 点提交...", flush=True)
    try:
        P.ele('xpath://button[contains(.,"提交")]', timeout=5).click()
        print("   提交✅", flush=True)
    except:
        print("   无提交", flush=True)
    time.sleep(5)
    # 回资产页验证
    try:
        P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
        time.sleep(6)
        body = P.ele('tag:body').text
        idx = body.find(song)
        if idx >= 0:
            st = '查看详情' if '查看详情' in body[idx:idx+60] else '发行全曲'
            print(f"   结果: {st}", flush=True)
    except:
        pass

print(f"\n=== {song} 完成 ===", flush=True)
