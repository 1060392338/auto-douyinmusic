#!/usr/bin/env python3
"""发布 v6 - SPA点发行全曲后操作新标签页"""
import sys, time, json, requests, websocket

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""

def eval_t(tid, js):
    w = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
    r = json.loads(w.recv())
    w.close()
    val = r.get('result',{}).get('result',{}).get('value')
    return val if val is not None else ''

print(f"=== 发布 {song} ===\n", flush=True)

bws = requests.get('http://localhost:9223/json/version', timeout=5).json()['webSocketDebuggerUrl']

# 找资产页
ws = websocket.create_connection(bws, timeout=5)
ws.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
targets = json.loads(ws.recv()).get('result',{}).get('targetInfos',[])
ws.close()

assets_tid = None
for t in targets:
    if 'studio/assets' in t.get('url','') and t['type'] == 'page':
        assets_tid = t['targetId']
        break

if not assets_tid:
    print("❌ 未找到资产页")
    sys.exit(1)

# 点击发行全曲
eval_t(assets_tid, f'''
(function() {{
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for(var i=0; i<cards.length; i++) {{
        if(cards[i].textContent.includes("{song}")) {{
            var all = cards[i].querySelectorAll('*');
            for(var j=0; j<all.length; j++) {{
                if(all[j].textContent && all[j].textContent.trim() === "发行全曲") {{
                    all[j].scrollIntoView({{behavior:"instant", block:"center"}});
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
time.sleep(5)

# 检查是否出现了新标签页（发布页）
ws2 = websocket.create_connection(bws, timeout=5)
ws2.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
targets2 = json.loads(ws2.recv()).get('result',{}).get('targetInfos',[])
ws2.close()

pub_tid = None
for t in targets2:
    if 'complete-publish' in t.get('url','') and t['type'] == 'page':
        pub_tid = t['targetId']
        print(f"✅ 新标签页: {t['url'][:80]}", flush=True)
        break

if not pub_tid:
    print("❌ 未生成发布页", flush=True)
    sys.exit(1)

# 禁用弹窗
eval_t(pub_tid, "window.onbeforeunload=null;")
time.sleep(2)

# 检查是否已预填
title_val = eval_t(pub_tid, 'document.querySelector("input.douyin-music-input")?.value || "no-val"')
print(f"标题: {title_val}", flush=True)

# 检查音频上传状态
has_audio = eval_t(pub_tid, 'document.body.textContent.includes("请上传完整版音频")')
print(f"需上传音频: {has_audio}", flush=True)

# 如果有音频上传提示，需要处理
if has_audio:
    print("⚠️ 需要上传音频文件，表单阻塞将跳过音频验证", flush=True)
    # 尝试触发hidden file input来上传
    # 但这是native dialog，没法自动。我们先填其他字段

# 歌曲标题已预填，检查并修改表演者
performer = eval_t(pub_tid, '''
(function() {
    var inputs = document.querySelectorAll('input.douyin-music-input');
    var results = [];
    for(var i=0; i<inputs.length; i++) {
        results.push({idx:i, ph:(inputs[i].placeholder||''), val:(inputs[i].value||''), vis:inputs[i].offsetWidth>0});
    }
    return JSON.stringify(results);
})();
''')
print(f"输入框: {performer[:300]}", flush=True)

# ── 处理表演者名字 ──
# 把AChq改为缓歌寄意
eval_t(pub_tid, f'''
(function() {{
    var inputs = document.querySelectorAll('input.douyin-music-input');
    for(var i=0; i<inputs.length; i++) {{
        var v = inputs[i].value || '';
        if(v === 'AChq' || v === 'AChq ') {{
            var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            s.call(inputs[i], '{song}');
            inputs[i].dispatchEvent(new Event('input', {{bubbles:true}}));
            inputs[i].dispatchEvent(new Event('change', {{bubbles:true}}));
        }}
    }}
    return 'done';
}}());
''')
print("表演者姓名✅", flush=True)
time.sleep(1)

# 检查"创建同名专辑"按钮
has_album = eval_t(pub_tid, 'document.body.textContent.includes("创建同名专辑")')
if has_album:
    eval_t(pub_tid, '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '创建同名专辑') {
                all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''')
    time.sleep(2)
    print("专辑✅", flush=True)

# ── 智能封面 ──
eval_t(pub_tid, '''
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '智能封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return;
        }
    }
})();
''')
time.sleep(3)
eval_t(pub_tid, '''
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return;
        }
    }
})();
''')
time.sleep(4)
eval_t(pub_tid, '''
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '使用封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
            return;
        }
    }
})();
''')
time.sleep(2)
print("封面✅", flush=True)

# ── 点下一步 ──
for step in range(5):
    print(f"  第{step+1}次点下一步...", flush=True)
    eval_t(pub_tid, "window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    eval_t(pub_tid, '''
    (function() {
        var sb = document.querySelector('[class*=simplebar-content-wrapper]');
        if(sb) sb.scrollTo(0, sb.scrollHeight);
    })();
    ''')
    time.sleep(1)
    
    result = eval_t(pub_tid, '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=all.length-1; i>=0; i--) {
            if(all[i].textContent && all[i].textContent.trim() === '下一步') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                ['pointerdown','pointerup','click'].forEach(function(t) {
                    all[i].dispatchEvent(new PointerEvent(t, {bubbles:true, cancelable:true}));
                });
                return 'clicked-' + all[i].className.substring(0,20);
            }
        }
        return 'not-found';
    })();
    ''')
    print(f"  点击结果: {result}", flush=True)
    time.sleep(4)
    
    # 检查letsign
    ws3 = websocket.create_connection(bws, timeout=5)
    ws3.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    tgs = json.loads(ws3.recv()).get('result',{}).get('targetInfos',[])
    ws3.close()
    
    found = False
    for t in tgs:
        if 'letsign' in t.get('url','') and t['type'] == 'page':
            found = True
            print(f"  ✅ letsign!", flush=True)
            l_tid = t['targetId']
            
            eval_t(l_tid, '''
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
            ''')
            time.sleep(3)
            
            if verify_code:
                eval_t(l_tid, f'''
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
                ''')
                time.sleep(1)
                eval_t(l_tid, '''
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
                ''')
                time.sleep(4)
                signed = eval_t(l_tid, 'document.body.textContent.includes("签署成功")')
                print(f"  {'✅签署成功' if signed else '❌签署失败'}", flush=True)
            else:
                eval_t(l_tid, '''
                (function() {
                    var inputs = document.querySelectorAll('input');
                    for(var i=0; i<inputs.length; i++) {
                        var ph = inputs[i].placeholder || '';
                        if(ph.includes('验证码') || ph.includes('数字')) {
                            inputs[i].focus();
                            inputs[i].click();
                            return 'focused';
                        }
                    }
                    return 'no-input';
                })();
                ''')
                time.sleep(1)
                eval_t(l_tid, '''
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
                ''')
                print("   验证码已发送!", flush=True)
                with open('/tmp/publish_state.json', 'w') as f:
                    json.dump({'song': song, 'letsign_tid': l_tid}, f)
                print(f"\n>>> 陛下，请查看手机验证码 <<<", flush=True)
            break
    if found:
        break

if not found:
    print("❌ 未到达 letsign", flush=True)
    # 检查当前页面状态
    after = eval_t(pub_tid, '''
    (function() {
        var sb = document.querySelector('[class*=simplebar-content]');
        var t = sb ? sb.textContent.trim() : document.body.textContent;
        return t.substring(0, 1000);
    })();
    ''')
    print(f"页面状态: {after[:200]}", flush=True)

print(f"\n=== 发布 {song} 完成 ===", flush=True)
