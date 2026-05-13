#!/usr/bin/env python3
"""
发布 v5 - 资产页内SPA导航到发布页（同一页面）
"""
import sys, time, json
import requests, websocket

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""

def get_bws():
    return requests.get('http://localhost:9223/json/version', timeout=5).json()['webSocketDebuggerUrl']

def eval_t(tid, js):
    w = websocket.create_connection(f'ws://localhost:9223/devtools/page/{tid}', timeout=10)
    w.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':js,'returnByValue':True,'awaitPromise':False}}))
    r = json.loads(w.recv())
    w.close()
    return r.get('result',{}).get('result',{}).get('value')

# 找assets页
bws = get_bws()
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

# 在资产页内找到对应歌曲的"发行全曲"并点击
print(f"=== 发布 {song} (SPA内导航) ===", flush=True)

clicked = eval_t(assets_tid, f'''
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
print(f"点击: {clicked}", flush=True)
time.sleep(6)

# 检查页面URL是否变了
cur_url = eval_t(assets_tid, 'window.location.href')
print(f"当前URL: {cur_url[:100]}", flush=True)

if 'complete-publish' not in cur_url:
    print("❌ SPA导航未完成，手动导航", flush=True)
    # 获取work-id
    wid = eval_t(assets_tid, f'''
    (function() {{
        var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
        for(var i=0; i<cards.length; i++) {{
            if(cards[i].textContent.includes("{song}")) {{
                return cards[i].getAttribute("data-work-id") || "";
            }}
        }}
        return "";
    }})();
    ''')
    print(f"work-id: {wid}", flush=True)
    if wid:
        eval_t(assets_tid, f"window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId={wid}';")
        time.sleep(5)
        cur_url = eval_t(assets_tid, 'window.location.href')
        print(f"导航后URL: {cur_url[:100]}", flush=True)

pub_tid = assets_tid  # 现在assets页已经变成发布页

# 页面状态检查
body_len = eval_t(pub_tid, 'document.body.textContent.length')
print(f"body长度: {body_len}", flush=True)

# 检查并填表单
error_msgs = eval_t(pub_tid, '''
JSON.stringify(Array.from(document.querySelectorAll('[class*=error], [class*=tip], [class*=warning]')).filter(e => e.textContent.trim().length > 0).slice(0,5).map(e => e.textContent.trim().substring(0, 40)))
''')
print(f"表单错误: {error_msgs}", flush=True)

# ── 填表单 ──
# 1. 音乐类型 - 点原创（第一个radio）
eval_t(pub_tid, '''
(function() {
    var radios = document.querySelectorAll('input[type=radio]');
    if(radios.length > 0) {
        radios[0].click();
        radios[0].checked = true;
        radios[0].dispatchEvent(new Event('change', {bubbles: true}));
        return 'done';
    }
    return 'no-radio';
})();
''')
print("原创✅", flush=True)
time.sleep(1)

# 2. 填歌曲标题（找input.visible + placeholder）
eval_t(pub_tid, f'''
(function() {{
    var inputs = document.querySelectorAll('input');
    for(var i=0; i<inputs.length; i++) {{
        var ph = inputs[i].placeholder || '';
        if(ph.includes('歌曲标题') || ph.includes('请输入')) {{
            inputs[i].focus();
            inputs[i].value = '';
            var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            s.call(inputs[i], '{song}');
            inputs[i].dispatchEvent(new Event('input', {{bubbles:true}}));
            inputs[i].dispatchEvent(new Event('change', {{bubbles:true}}));
            return 'filled';
        }}
    }}
    // 也检查div contenteditable
    var editables = document.querySelectorAll('[contenteditable=true]');
    for(var i=0; i<editables.length; i++) {{
        editables[i].textContent = '{song}';
        editables[i].dispatchEvent(new Event('input', {{bubbles:true}}));
        return 'filled-editable';
    }}
    return 'no-input, count=' + document.querySelectorAll('input').length;
}})();
''')
print(f"歌名: {song}✅", flush=True)
time.sleep(1)

# 3. 智能封面
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

# ── 检查是否有上传完整版的提示 ──
has_audio_error = eval_t(pub_tid, 'document.body.textContent.includes("请上传完整版音频")')
print(f"需要上传音频: {has_audio_error}", flush=True)

# ── 点下一步 ──
for step in range(3):  # 最多尝试3次下一步
    print(f"  第{step+1}次点下一步...", flush=True)
    # 滚动到底部
    eval_t(pub_tid, 'window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(1)
    # 滚动simplebar容器
    eval_t(pub_tid, '''
    (function() {
        var sb = document.querySelector('[class*=simplebar-content-wrapper]');
        if(sb) sb.scrollTo(0, sb.scrollHeight);
        return sb ? 'scrolled' : 'no-sb';
    })();
    ''')
    time.sleep(1)
    
    eval_t(pub_tid, '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '下一步') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(t) {
                    all[i].dispatchEvent(new PointerEvent(t, {bubbles:true, cancelable:true}));
                });
                return 'clicked-next';
            }
        }
        return 'no-next-btn';
    })();
    ''')
    time.sleep(4)
    
    # 检查letsign
    ws2 = websocket.create_connection(bws, timeout=5)
    ws2.send(json.dumps({'id':1,'method':'Target.getTargets','params':{}}))
    tgs = json.loads(ws2.recv()).get('result',{}).get('targetInfos',[])
    ws2.close()
    
    found_letsign = False
    for t in tgs:
        if 'letsign' in t.get('url','') and t['type'] == 'page':
            found_letsign = True
            print(f"  ✅ letsign出现!", flush=True)
            
            # 处理签署...
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
                print(f"  签署: {'✅成功' if signed else '❌失败'}", flush=True)
            else:
                # 聚焦 + 获取验证码
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
                print("   验证码已发!", flush=True)
                with open('/tmp/publish_state.json', 'w') as f:
                    json.dump({'song': song, 'letsign_tid': l_tid}, f)
                print(f"\n>>> 陛下，请查看手机验证码 <<<", flush=True)
            break
    
    if found_letsign:
        break
    
    # 检查当前页面文本是否有变化
    after_text = eval_t(pub_tid, 'document.body.textContent.substring(500, 1000).replace(/[\\s]+/g," ").trim()')
    print(f"  页面: {after_text[:100]}", flush=True)

print(f"\n=== 发布 {song} 完成 ===", flush=True)
