#!/usr/bin/env python3
"""发布 v13 - 陛下说Step2自动就好"""
import sys, time, json, requests, websocket as wsmod
from DrissionPage import ChromiumPage

song = sys.argv[1] if len(sys.argv) > 1 else "纸鸢远"
print(f"=== 发布 {song} ===", flush=True)

time.sleep(2)
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

# 已在资产页，点发行全曲
P.run_js(f'''
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
time.sleep(6)

# 找发布页
P2 = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)
for tab in P2.get_tabs():
    if 'complete-publish' in tab.url:
        P = tab
        break
P.run_js("window.onbeforeunload=null")
time.sleep(2)

# 下一步→Step2（自动）
P.ele('xpath://button[contains(.,"下一步")]', timeout=5).click()
print("2. 下一步→Step2✅", flush=True)
time.sleep(4)

# 下一步→Step3（陛下说等一会儿直接点）
P.run_js('''
(function() {
    window.scrollTo(0, document.body.scrollHeight);
    setTimeout(function() {
        var all = document.querySelectorAll('*');
        var found = [];
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '下一步') {
                var r = all[i].getBoundingClientRect();
                if(r.width > 0 && r.height > 0) found.push(all[i]);
            }
        }
        if(found.length > 0) {
            found[found.length-1].scrollIntoView({behavior:"instant", block:"center"});
            found[found.length-1].dispatchEvent(new PointerEvent('click', {bubbles:true, cancelable:true}));
        }
    }, 1000);
})();
''')
time.sleep(6)
print("3. 下一步→Step3✅", flush=True)

# 找letsign
bws = requests.get('http://localhost:9223/json/version', timeout=5).json()['webSocketDebuggerUrl']
ws = wsmod.create_connection(bws, timeout=5)
ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
r = json.loads(ws.recv())
ws.close()

letsign_tid = None
for t in r.get('result',{}).get('targetInfos',[]):
    if 'letsign' in t.get('url',''):
        letsign_tid = t['targetId']
        print(f"4. ✅ letsign!", flush=True)
        break

if letsign_tid:
    def e(js):
        w = wsmod.create_connection(f'ws://localhost:9223/devtools/page/{letsign_tid}', timeout=10)
        w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
        r2 = json.loads(w.recv())
        w.close()
        v = r2.get('result',{}).get('result',{}).get('value')
        return v if v is not None else ''
    
    # 批量签署
    e('document.querySelector("button")?.click()')
    time.sleep(3)
    
    # 聚焦输入框
    e('document.querySelector("input")?.focus()')
    time.sleep(1)
    
    # 获取验证码
    e('document.querySelector(".ds-captcha-next__form-send")?.click()')
    print("   验证码已发送！", flush=True)
    
    with open('/tmp/pub_state.json', 'w') as f:
        json.dump({'song': song, 'letsign_tid': letsign_tid}, f)
    print(f"\n>>> 陛下，请查看手机验证码 ({song}) <<<", flush=True)
else:
    btns = P.eles('tag:button')
    print(f"4. 无letsign:{[b.text.strip() for b in btns if b.text.strip()]}", flush=True)
