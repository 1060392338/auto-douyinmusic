#!/usr/bin/env python3
"""
发布 v9 - DrissionPage直连操作发布表单
从资产页点"发行全曲"后，用ChromiumPage操作新标签页
"""
import sys, time, os, signal, json, requests
from DrissionPage import ChromiumPage

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"

def _cleanup(signum, frame):
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

print(f"=== 发布 {song} ===\n", flush=True)

# 第1步：清理旧发布页
bws = 'http://localhost:9223'
ver = requests.get(f'{bws}/json/version', timeout=5).json()
b_ws_url = ver['webSocketDebuggerUrl']

import websocket
def send_cdp(method, params=None):
    if params is None: params = {}
    ws = websocket.create_connection(b_ws_url, timeout=5)
    ws.send(json.dumps({'id':1,'method':method,'params':params}))
    r = json.loads(ws.recv())
    ws.close()
    return r

# 关闭所有旧发布页
targets = send_cdp('Target.getTargets').get('result',{}).get('targetInfos',[])
for t in targets:
    if 'complete-publish' in t.get('url',''):
        send_cdp('Target.closeTarget', {'targetId': t['targetId']})
        print(f"  清理旧发布页", flush=True)

# 第2步：从资产页点"发行全曲"
assets_tid = None
for t in targets:
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']
        break

if not assets_tid:
    print("❌ 未找到资产页")
    sys.exit(1)

# 点击发行全曲
def eval_js(tid, js):
    r = send_cdp_on_page(tid, 'Runtime.evaluate', {'expression': js, 'returnByValue': True, 'awaitPromise': False})
    return r.get('result',{}).get('result',{}).get('value')

def send_cdp_on_page(tid, method, params=None):
    if params is None: params = {}
    ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    ws.send(json.dumps({'id':1,'method':method,'params':params}))
    r = json.loads(ws.recv())
    ws.close()
    return r

eval_js(assets_tid, f'''
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
print("✅ 已点发行全曲", flush=True)
time.sleep(5)

# 找新发布页
targets2 = send_cdp('Target.getTargets').get('result',{}).get('targetInfos',[])
pub_tid = None
for t in targets2:
    if 'complete-publish' in t.get('url','') and t['type'] == 'page':
        pub_tid = t['targetId']
        break

if not pub_tid:
    print("❌ 发布页未生成")
    sys.exit(1)

pub_url = None
for t in targets2:
    if t.get('targetId') == pub_tid:
        pub_url = t.get('url','')
        break
print(f"✅ 发布页: {pub_url[:80]}", flush=True)

# 第3步：用ChromiumPage连接并操作发布页
# 先杀掉旧的ChromiumPage连接（如果存在）
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 切换到发布页标签 - DrissionPage默认当前标签页
# 先获取所有标签页
tabs = P.get_tabs()
print(f"标签页: {len(tabs)}", flush=True)
for i, tab in enumerate(tabs):
    url = tab.url
    if 'complete-publish' in url:
        P = tab  # 切换到发布页
        print(f"  切换到发布页 {i}: {url[:60]}", flush=True)
        break

time.sleep(2)

# 禁用弹窗
P.run_js("window.onbeforeunload=null")
time.sleep(1)

print("\n=== 开始操作表单 ===", flush=True)

# 获取页面文本
body = P.ele('tag:body').text
has_publish = '发行全曲' in body
has_next = '下一步' in body
print(f"页面含发行全曲: {has_publish}", flush=True)
print(f"页面含下一步: {has_next}", flush=True)

# 尝试直接点击"下一步"按钮 - 用多种方式
for attempt in range(3):
    print(f"\n尝试 {attempt+1}:", flush=True)
    
    # 方法1: DrissionPage的ele().click()
    try:
        next_btn = P.ele('xpath://button[contains(.,"下一步")]', timeout=3)
        if next_btn:
            next_btn.click()
            print("  DrissionPage click✅", flush=True)
            time.sleep(4)
    except:
        print("  DrissionPage click❌", flush=True)
    
    # 检查是否推进了
    has_auth = '授权信息' in P.ele('tag:body').text
    print(f"  有授权信息: {has_auth}", flush=True)
    if has_auth:
        print("✅ 已进入Step2!", flush=True)
        break
    
    # 方法2: JS dispatchEvent
    P.run_js('''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=all.length-1; i>=0; i--) {
            if(all[i].textContent && all[i].textContent.trim() === '下一步') {
                all[i].scrollIntoView({behavior:"instant", block:"center"});
                ["pointerdown","pointerup","mousedown","mouseup","click"].forEach(function(t) {
                    all[i].dispatchEvent(new PointerEvent(t, {bubbles:true, cancelable:true}));
                });
                return;
            }
        }
    })();
    ''')
    print("  JS dispatchEvent✅", flush=True)
    time.sleep(4)
    
    # 再检查
    body2 = P.ele('tag:body').text
    has_auth2 = '授权信息' in body2
    print(f"  有授权信息: {has_auth2}", flush=True)
    if has_auth2:
        print("✅ 已进入Step2!", flush=True)
        break
    
    # 方法3: 滚动到最底部再点
    P.run_js('''
    (function() {
        var sb = document.querySelector('[class*=simplebar-content-wrapper]');
        if(sb) sb.scrollTo(0, sb.scrollHeight);
        window.scrollTo(0, document.body.scrollHeight);
        setTimeout(function() {
            var btns = document.querySelectorAll('button');
            for(var i=btns.length-1; i>=0; i--) {
                if(btns[i].textContent.trim() === '下一步') {
                    btns[i].click();
                    return;
                }
            }
        }, 500);
    })();
    ''')
    print("  原生.click()✅", flush=True)
    time.sleep(4)

# 最终检查
body_final = P.ele('tag:body').text
print(f"\n最终步骤: {'Step2' if '授权信息' in body_final else 'Step1'}", flush=True)
if 'letsign' in str(P.run_js('return window.location.href') or '').lower():
    print("✅ letsign页面!", flush=True)
elif '签署' in body_final:
    print("✅ 签署页面!", flush=True)

print(f"\n=== 发布 {song} 完成 ===", flush=True)
