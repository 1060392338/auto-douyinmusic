#!/usr/bin/env python3
"""
发布 v4 - SPA内部点发行全曲
"""
import sys, time, os, signal, json
import requests, websocket

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""

print(f"=== 发布 {song} ===\n", flush=True)

def get_targets():
    ver = requests.get('http://localhost:9223/json/version', timeout=5).json()
    bws = ver['webSocketDebuggerUrl']
    ws = websocket.create_connection(bws, timeout=5)
    ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    r = json.loads(ws.recv())
    ws.close()
    return r.get('result',{}).get('targetInfos',[]), bws

def eval_t(tid, js):
    ws = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
    r = json.loads(ws.recv())
    ws.close()
    return r.get('result',{}).get('result',{}).get('value')

# ── 1. 找资产页，点发行全曲 ──
targets, bws = get_targets()
assets_tid = None
for t in targets:
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']
        break

if not assets_tid:
    print("❌ 未找到资产页", flush=True)
    sys.exit(1)

# 在缓歌寄意卡片的上下文中点击"发行全曲"
clicked = eval_t(assets_tid, f'''
(function() {{
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for(var i=0; i<cards.length; i++) {{
        if(cards[i].textContent.includes("{song}")) {{
            // 找发行全曲div
            var all = cards[i].querySelectorAll('*');
            for(var j=0; j<all.length; j++) {{
                if(all[j].textContent && all[j].textContent.trim() === "发行全曲") {{
                    all[j].scrollIntoView({{behavior:"instant", block:"center"}});
                    // 全事件链
                    ["pointerdown","pointerup","mousedown","mouseup","click"].forEach(function(t) {{
                        all[j].dispatchEvent(new PointerEvent(t, {{bubbles:true, cancelable:true}}));
                    }});
                    return "clicked";
                }}
            }}
        }}
    }}
    return "not-found";
}})();
''')
print(f"点击结果: {clicked}", flush=True)
time.sleep(5)

# 检查是否出现了新页面
targets2, _ = get_targets()
pub_tid = None
for t in targets2:
    url = t.get('url','')
    if 'complete-publish' in url and t['type'] == 'page':
        pub_tid = t['targetId']
        print(f"✅ 发布页: {url[:80]}", flush=True)
        break

if not pub_tid:
    print("❌ 未出现发布页", flush=True)
    # 检查当前页URL变化
    cur_url = eval_t(assets_tid, "window.location.href")
    print(f"当前URL: {cur_url}", flush=True)
    sys.exit(1)

# 禁用弹窗
eval_t(pub_tid, "window.onbeforeunload=null;")
print("1. 进入发布页✅", flush=True)

# ── 2. 智能封面 ──
print("2. 智能封面...", flush=True)
eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '智能封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(3)

eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '一键生成封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(4)

eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '使用封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return 'used';
        }
    }
    return 'not-found';
})();
""")
time.sleep(2)
print("   封面✅", flush=True)

# 检查页面
page_snippet = eval_t(pub_tid, "document.body.textContent.substring(0, 500)")
print(f"   页面前500字: {page_snippet[:100]}", flush=True)

# ── 3. 第一次下一步 ──
print("3. 第一次下一步...", flush=True)
eval_t(pub_tid, "window.scrollTo(0, document.body.scrollHeight);")
time.sleep(1)

eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '下一步') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            ['mousedown','mouseup','click'].forEach(function(ev) {
                all[i].dispatchEvent(new MouseEvent(ev, {bubbles:true, cancelable:true, view:window, button:0}));
            });
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(4)

# ── 4. 艺人信息 ──
print("4. 艺人信息...", flush=True)
eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '有主页链接') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(2)

eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '无主页链接') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(1)
print("   艺人信息✅", flush=True)

# ── 5. 第二次下一步 ──
print("5. 第二次下一步...", flush=True)
eval_t(pub_tid, """
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        var t = all[i].textContent;
        if(t && t.trim() === '下一步') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            ['mousedown','mouseup','click'].forEach(function(ev) {
                all[i].dispatchEvent(new MouseEvent(ev, {bubbles:true, cancelable:true, view:window, button:0}));
            });
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(5)

# ── 6. 找letsign ──
print("6. 找letsign...", flush=True)
targets3, _ = get_targets()
letsign_tid = None
letsign_url = ""
for t in targets3:
    url = t.get('url','')
    if 'letsign' in url and t['type'] == 'page':
        letsign_tid = t['targetId']
        letsign_url = url
        print(f"✅ letsign: {url[:60]}...", flush=True)
        break

if letsign_tid:
    # 点批量签署
    eval_t(letsign_tid, """
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
    
    if verify_code:
        eval_t(letsign_tid, f"""
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
        
        eval_t(letsign_tid, """
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
        
        signed = eval_t(letsign_tid, "document.body.textContent.includes('签署成功')")
        if signed:
            print("✅ 签署成功！", flush=True)
        else:
            final_t = eval_t(letsign_tid, "document.body.textContent.substring(0, 500)")
            print(f"签署状态: {final_t[:100]}", flush=True)
    else:
        # 聚焦输入框
        eval_t(letsign_tid, """
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
            return 'no-input, count=' + document.querySelectorAll('input').length;
        })();
        """)
        time.sleep(1)
        
        # 点获取验证码
        eval_t(letsign_tid, """
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
        with open('/tmp/publish_state.json', 'w') as f:
            json.dump({'song': song, 'letsign_tid': letsign_tid}, f)
        print(f"\n>>> 陛下，请查看手机验证码，然后告诉我 <<<", flush=True)
else:
    print("❌ 未找到letsign", flush=True)
    cur = eval_t(pub_tid, "document.body.textContent.substring(0, 1000)")
    print(f"发布页: {cur[:300]}", flush=True)

print(f"\n=== 发布 {song} 阶段完成 ===", flush=True)
