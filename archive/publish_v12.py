#!/usr/bin/env python3
"""
发布 v12 - 完整流程不关页面
用法: python3 publish_v12.py <歌名> [验证码]
"""
import sys, time, json, requests, os
from DrissionPage import ChromiumPage

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
code = sys.argv[2] if len(sys.argv) > 2 else ""

print(f"=== 发布 {song} ===\n", flush=True)

# 连接Chrome（不kill任何页面）
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 找到已有资产页或新开一个
tabs = P.get_tabs()
assets_tab = None
for tab in tabs:
    if 'studio/assets' in tab.url:
        assets_tab = tab
        break

if not assets_tab:
    P.run_js("window.location.href='https://music.douyin.com/studio/assets'")
    time.sleep(6)
    assets_tab = P

# 在资产页点发行全曲
assets_tab.run_js(f'''
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

# 找发布页标签并切换
for tab in P.get_tabs():
    if 'complete-publish' in tab.url:
        P = tab
        print(f"   切换到发布页", flush=True)
        break
time.sleep(2)

# 禁用弹窗（不关页面）
P.run_js("window.onbeforeunload=null")
time.sleep(1)

# 下一步1 → Step2
try:
    P.ele('xpath://button[contains(.,"下一步")]', timeout=5).click()
    print("2. 下一步→Step2✅", flush=True)
except:
    print("   无下一步", flush=True)
time.sleep(4)

# 艺人信息
for txt in ['有主页链接', '无主页链接']:
    try:
        el = P.ele(f'xpath://*[contains(text(),"{txt}")]', timeout=3)
        if el and el.offsetWidth > 0:
            el.click()
            time.sleep(1)
    except:
        pass
print("3. 艺人信息✅", flush=True)

# 下一步2 → Step3（用JS找可见的下一步并点击）
try:
    P.run_js('''
    (function() {
        window.scrollTo(0, document.body.scrollHeight);
        var sb = document.querySelector('[class*=simplebar-content-wrapper]');
        if(sb) sb.scrollTo(0, sb.scrollHeight);
        setTimeout(function() {
            // 从后往前找可见的"下一步"按钮（Step2的在上一步后面）
            var all = document.querySelectorAll('*');
            var found = [];
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '下一步') {
                    var r = all[i].getBoundingClientRect();
                    if(r.width > 0 && r.height > 0) found.push(all[i]);
                }
            }
            // 点最后一个可见的（Step2的）
            if(found.length > 0) {
                found[found.length-1].scrollIntoView({behavior:"instant", block:"center"});
                found[found.length-1].dispatchEvent(new PointerEvent('click', {bubbles:true, cancelable:true}));
            }
        }, 1000);
    })();
    ''')
    time.sleep(4)
    print("4. 下一步→Step3✅", flush=True)
except Exception as e:
    print(f"   下一步2错误: {e}", flush=True)
time.sleep(5)

# 检查有没有letsign或提交
import websocket as ws_mod
ver = requests.get('http://localhost:9223/json/version', timeout=5).json()
bws = ver['webSocketDebuggerUrl']
ws = ws_mod.create_connection(bws, timeout=5)
ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
targets = json.loads(ws.recv()).get('result',{}).get('targetInfos',[])
ws.close()

letsign_tid = None
for t in targets:
    if 'letsign' in t.get('url',''):
        letsign_tid = t['targetId']
        break

if letsign_tid:
    print("5. letsign✅", flush=True)
    # 用CDP操作letsign
    def cdp_eval(tid, js):
        w = ws_mod.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
        w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
        r2 = json.loads(w.recv())
        w.close()
        return r2.get('result',{}).get('result',{}).get('value')
    
    # 点批量签署
    cdp_eval(letsign_tid, '''
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
    cdp_eval(letsign_tid, '''
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
    
    cdp_eval(letsign_tid, '''
    (function() {
        var el = document.querySelector('.ds-captcha-next__form-send');
        if(el) { el.click(); return 'clicked'; }
        return 'not-found';
    })();
    ''')
    print("   验证码已发送!", flush=True)
    
    if code:
        cdp_eval(letsign_tid, f'''
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
                            btns[j].click();
                        }}
                    }}
                    return 'done';
                }}
            }}
            return 'no-input';
        }})();
        ''')
        time.sleep(5)
        result = cdp_eval(letsign_tid, 'document.body.textContent.includes("签署成功")')
        print(f"   签署: {'✅成功' if result else '❌失败'}", flush=True)
        if result:
            print("   等待自动跳转...", flush=True)
            time.sleep(8)
    else:
        with open('/tmp/pub_state.json', 'w') as f:
            json.dump({'song': song, 'letsign_tid': letsign_tid}, f)
        print(f"\n>>> 陛下，请查看手机验证码 ({song}) <<<", flush=True)
else:
    # 无letsign找提交
    print("5. 无letsign, 找提交...", flush=True)
    try:
        # 看看当前有哪些按钮
        btns = P.eles('tag:button')
        btn_texts = [b.text.strip() for b in btns if b.text.strip()]
        print(f"   按钮: {btn_texts}", flush=True)
        
        if '提交' in btn_texts:
            P.ele('xpath://button[contains(.,"提交")]', timeout=3).click()
            print("   提交✅", flush=True)
            time.sleep(6)
        else:
            # 可能已经提交完成，回资产页验证
            pass
    except:
        print("   无提交", flush=True)
    
    # 回资产页验证
    try:
        P.run_js("window.onbeforeunload=null")
        P.run_js("window.location.href='https://music.douyin.com/studio/assets'")
        time.sleep(6)
        body = P.ele('tag:body').text
        idx = body.find(song)
        if idx >= 0:
            st = '查看详情' if '查看详情' in body[idx:idx+60] else '发行全曲'
            print(f"   结果: {st}", flush=True)
    except:
        print("   验证异常", flush=True)

# 强制关闭所有发布页
import websocket as ws_close
ver_c = requests.get('http://localhost:9223/json/version', timeout=5).json()
ws_c = ws_close.create_connection(ver_c['webSocketDebuggerUrl'], timeout=5)
ws_c.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
targets_c = json.loads(ws_c.recv()).get('result',{}).get('targetInfos',[])
for t in targets_c:
    if 'complete-publish' in t.get('url',''):
        ws_c.send(json.dumps({'id':2,'method':'Target.closeTarget','params':{'targetId':t['targetId']}}))
        json.loads(ws_c.recv())
        print(f"   关闭发布页: {t['url'][:40]}", flush=True)
ws_c.close()

print(f"\n=== {song} 完成 ===", flush=True)
