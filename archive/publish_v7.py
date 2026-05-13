#!/usr/bin/env python3
"""发布工作流：从资产页点发行全曲 → 走完表单 → 签署"""
import sys, time, json, requests, websocket, os

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""
state_file = sys.argv[3] if len(sys.argv) > 3 else ""

bws = requests.get('http://localhost:9223/json/version', timeout=5).json()['webSocketDebuggerUrl']

def eval_t(tid, js):
    w = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
    r = json.loads(w.recv())
    w.close()
    val = r.get('result',{}).get('result',{}).get('value')
    return val if val is not None else ''

# 状态文件模式：从assets页点发行全曲 -> 创建发布页
if state_file == 'init':
    # 清理旧发布页
    ws = websocket.create_connection(bws, timeout=5)
    ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    r = json.loads(ws.recv())
    for t in r.get('result',{}).get('targetInfos',[]):
        if 'complete-publish' in t.get('url','') and t['type'] == 'page':
            ws.send(json.dumps({'id':2,'method':'Target.closeTarget','params':{'targetId':t['targetId']}}))
            json.loads(ws.recv())
    ws.close()
    time.sleep(2)
    
    # 找资产页
    ws = websocket.create_connection(bws, timeout=5)
    ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    r = json.loads(ws.recv())
    ws.close()
    
    assets_tid = None
    for t in r.get('result',{}).get('targetInfos',[]):
        if 'studio/assets' in t.get('url','') and t['type'] == 'page':
            assets_tid = t['targetId']
            break
    
    if not assets_tid:
        print("❌ 未找到资产页")
        sys.exit(1)
    
    # 点发行全曲
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
    time.sleep(5)
    print("✅ 已点发行全曲，等待新标签页...", flush=True)
    
    # 找新发布的标签页
    ws = websocket.create_connection(bws, timeout=5)
    ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    r = json.loads(ws.recv())
    ws.close()
    
    pub_tid = None
    for t in r.get('result',{}).get('targetInfos',[]):
        if 'complete-publish' in t.get('url','') and t['type'] == 'page':
            pub_tid = t['targetId']
            break
    
    if not pub_tid:
        print("❌ 未生成发布页")
        sys.exit(1)
    
    # 保存状态
    with open('/tmp/pub_state.json', 'w') as f:
        json.dump({'song': song, 'pub_tid': pub_tid}, f)
    print(f"✅ 发布页就绪: {pub_tid}", flush=True)
    sys.exit(0)

# 正常模式：读取状态，走流程
if not state_file:
    # 加载状态
    try:
        with open('/tmp/pub_state.json') as f:
            st = json.load(f)
        song = st.get('song', song)
        pub_tid = st.get('pub_tid')
    except:
        print("❌ 未找到状态文件，请先用 init 模式")
        sys.exit(1)
else:
    # 直接从状态文件读取
    with open(state_file) as f:
        st = json.load(f)
    song = st.get('song', song)
    pub_tid = st.get('pub_tid') or st.get('letsign_tid')

print(f"=== 发布 {song} ===", flush=True)

if not pub_tid:
    print("❌ 无发布页ID")
    sys.exit(1)

# 1. 禁用弹窗
eval_t(pub_tid, "window.onbeforeunload=null")
time.sleep(1)

# 2. 检查是否有音频错误
has_audio_err = str(eval_t(pub_tid, 'document.body.textContent.includes("请上传完整版音频")'))
if 'True' in has_audio_err:
    print("⚠️ 需要上传音频，跳过", flush=True)
else:
    print("音频已就绪✅", flush=True)

# 3. 智能封面
for txt, wait in [('智能封面',2),('一键生成封面',3),('使用封面',2)]:
    eval_t(pub_tid, f'''
    (function() {{
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {{
            if(all[i].textContent && all[i].textContent.trim() === '{txt}') {{
                all[i].dispatchEvent(new MouseEvent('click', {{bubbles:true, cancelable:true, view:window}}));
                return;
            }}
        }}
    }})();
    ''')
    time.sleep(wait)
print("封面✅", flush=True)

# 4. 添加表演者
eval_t(pub_tid, '''
(function() {
    var btns = document.querySelectorAll('button');
    var count = 0;
    for(var i=0; i<btns.length; i++) {
        if(btns[i].textContent.trim() === '添加自己') {
            count++;
            if(count === 1) {
                btns[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                return;
            }
        }
    }
})();
''')
time.sleep(2)
print("表演者✅", flush=True)

# 5. 创建同名专辑
if str(eval_t(pub_tid, 'document.body.textContent.includes("创建同名专辑")')) == 'True':
    for txt in ['创建同名专辑']:
        eval_t(pub_tid, f'''
        (function() {{
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {{
                if(all[i].textContent && all[i].textContent.trim() === '{txt}') {{
                    all[i].dispatchEvent(new MouseEvent('click', {{bubbles:true, cancelable:true, view:window, button:0}}));
                    return;
                }}
            }}
        }})();
        ''')
        time.sleep(2)
    print("专辑✅", flush=True)

# 6. 第一次下一步
print("下一步1...", flush=True)
eval_t(pub_tid, "window.scrollTo(0, document.body.scrollHeight)")
time.sleep(1)
eval_t(pub_tid, '''
(function() {
    var sb = document.querySelector('[class*=simplebar-content-wrapper]');
    if(sb) sb.scrollTo(0, sb.scrollHeight);
})();
''')
time.sleep(1)
eval_t(pub_tid, '''
(function() {
    var all = document.querySelectorAll('*');
    for(var i=all.length-1; i>=0; i--) {
        if(all[i].textContent && all[i].textContent.trim() === '下一步') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            ['pointerdown','pointerup','click'].forEach(function(t) {
                all[i].dispatchEvent(new PointerEvent(t, {bubbles:true, cancelable:true}));
            });
            return;
        }
    }
})();
''')
time.sleep(5)

# 7. 艺人信息
has_artist = str(eval_t(pub_tid, 'document.body.textContent.includes("有主页链接")'))
if 'True' in has_artist:
    for txt in ['有主页链接','无主页链接']:
        eval_t(pub_tid, f'''
        (function() {{
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {{
                if(all[i].textContent && all[i].textContent.trim() === '{txt}') {{
                    all[i].dispatchEvent(new MouseEvent('click', {{bubbles:true, cancelable:true, view:window, button:0}}));
                    return;
                }}
            }}
        }})();
        ''')
        time.sleep(2)
    print("艺人信息✅", flush=True)

# 8. 第二次下一步
print("下一步2...", flush=True)
eval_t(pub_tid, "window.scrollTo(0, document.body.scrollHeight)")
time.sleep(1)
eval_t(pub_tid, '''
(function() {
    var all = document.querySelectorAll('*');
    for(var i=all.length-1; i>=0; i--) {
        if(all[i].textContent && all[i].textContent.trim() === '下一步') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            ['pointerdown','pointerup','click'].forEach(function(t) {
                all[i].dispatchEvent(new PointerEvent(t, {bubbles:true, cancelable:true}));
            });
            return;
        }
    }
})();
''')
time.sleep(5)

# 9. 找letsign
ws = websocket.create_connection(bws, timeout=5)
ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
r = json.loads(ws.recv())
ws.close()

letsign_tid = None
for t in r.get('result',{}).get('targetInfos',[]):
    if 'letsign' in t.get('url','') and t['type'] == 'page':
        letsign_tid = t['targetId']

if letsign_tid:
    print("✅ letsign!", flush=True)
    eval_t(letsign_tid, '''
    (function() {
        var btns = document.querySelectorAll('button');
        for(var i=0; i<btns.length; i++) {
            if(btns[i].textContent.trim() === '批量签署') {
                btns[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                return;
            }
        }
    })();
    ''')
    time.sleep(3)
    
    if verify_code:
        eval_t(letsign_tid, f'''
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
                    return;
                }}
            }}
        }})();
        ''')
        time.sleep(1)
        eval_t(letsign_tid, '''
        (function() {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                if(all[i].textContent && all[i].textContent.trim() === '确定') {
                    all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                    return;
                }
            }
        })();
        ''')
        time.sleep(4)
        signed = eval_t(letsign_tid, 'document.body.textContent.includes("签署成功")')
        print(f"{'✅ 签署成功！' if signed else '❌ 签署失败'}", flush=True)
    else:
        eval_t(letsign_tid, '''
        (function() {
            var inputs = document.querySelectorAll('input');
            for(var i=0; i<inputs.length; i++) {
                var ph = inputs[i].placeholder || '';
                if(ph.includes('验证码') || ph.includes('数字')) {
                    inputs[i].focus();
                    inputs[i].click();
                    return;
                }
            }
        })();
        ''')
        time.sleep(1)
        eval_t(letsign_tid, '''
        (function() {
            var all = document.querySelectorAll('*');
            for(var i=0; i<all.length; i++) {
                var t = all[i].textContent;
                if(t && t.trim() === '获取验证码') {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                    return;
                }
            }
        })();
        ''')
        print("   验证码已发送!", flush=True)
        print(f"\n>>> 陛下，请查看手机验证码 <<<", flush=True)
else:
    print("❌ 无letsign", flush=True)

print("\n=== 完成 ===", flush=True)
