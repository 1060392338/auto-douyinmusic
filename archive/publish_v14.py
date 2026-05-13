#!/usr/bin/env python3
"""发布 v14 - 极简版"""
import sys, time, json, requests, websocket as wsmod
from DrissionPage import ChromiumPage

song = sys.argv[1] if len(sys.argv) > 1 else "纸鸢远"
print(f"=== 发布 {song} ===", flush=True)

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

# 关掉旧的发布页
ver = requests.get('http://localhost:9223/json/version', timeout=5).json()
ws = wsmod.create_connection(ver['webSocketDebuggerUrl'], timeout=5)
ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
r = json.loads(ws.recv())
for t in r.get('result',{}).get('targetInfos',[]):
    if 'complete-publish' in t.get('url',''):
        ws.send(json.dumps({'id':2,'method':'Target.closeTarget','params':{'targetId':t['targetId']}}))
        json.loads(ws.recv())
ws.close()
time.sleep(1)

# 打开资产页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
time.sleep(6)

# 点发行全曲
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

# 第一步：点下一步
P.ele('xpath://button[contains(.,"下一步")]', timeout=5).click()
print("2. 下一步→Step2✅", flush=True)
time.sleep(5)

# 第二步：再点下一步（从Step2到Step3）
# 先滚动到底部
P.run_js("window.scrollTo(0, document.body.scrollHeight)")
time.sleep(2)

# 找所有可见的下一步按钮，点最后一个
btns = P.eles('tag:button')
visible_next = []
for b in btns:
    if b.text.strip() == '下一步':
        try:
            r = b.run_js('this.getBoundingClientRect()')
            if r and r.get('width',0) > 0 and r.get('height',0) > 0:
                visible_next.append(b)
        except:
            pass

if visible_next:
    btn = visible_next[-1]
    btn.run_js('this.scrollIntoView({behavior:"instant", block:"center"})')
    time.sleep(1)
    btn.click()
    print(f"3. 下一步→Step3✅", flush=True)
else:
    print("3. 无下一步按钮", flush=True)
time.sleep(6)

# 检查letsign
ws2 = wsmod.create_connection(ver['webSocketDebuggerUrl'], timeout=5)
ws2.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
r2 = json.loads(ws2.recv())
ws2.close()
for t in r2.get('result',{}).get('targetInfos',[]):
    if 'letsign' in t.get('url',''):
        print(f"4. ✅ letsign!", flush=True)
        l_tid = t['targetId']
        
        def e(js):
            w = wsmod.create_connection(f'ws://localhost:9223/devtools/page/{l_tid}', timeout=10)
            w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
            r3 = json.loads(w.recv())
            w.close()
            return r3.get('result',{}).get('result',{}).get('value')
        
        # 批量签署
        e('document.querySelector("button")?.click()')
        time.sleep(3)
        e('document.querySelector("input")?.focus()')
        time.sleep(1)
        e('document.querySelector(".ds-captcha-next__form-send")?.click()')
        print("   验证码已发送!", flush=True)
        
        with open('/tmp/pub_state.json', 'w') as f:
            json.dump({'song': song, 'letsign_tid': l_tid}, f)
        print(f"\n>>> 陛下，请查看手机验证码 ({song}) <<<", flush=True)
        break
else:
    btns = P.eles('tag:button')
    print(f"4. 无letsign:{[b.text.strip() for b in btns if b.text.strip()]}", flush=True)
