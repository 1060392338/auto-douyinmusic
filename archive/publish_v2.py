#!/usr/bin/env python3
"""
发布 v2 - URL直连发布页方式
用法: python3 publish_v2.py <歌名> [验证码]
"""
import sys, time, os, signal, json
from DrissionPage import ChromiumPage

def _cleanup(signum, frame):
    print("\n⚠️ 清理中...", flush=True)
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

P = ChromiumPage(addr_or_opts="127.0.0.1:9223")
song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""

def js(code):
    for _ in range(3):
        try:
            return P.run_js(code)
        except:
            try: P.handle_alert(accept=True)
            except: pass
            time.sleep(1)
    return None

print(f"=== 发布 {song} ===\n", flush=True)

# ── 1. 导航到资产页取 work-id ──
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
time.sleep(6)

# 取work-id和封面
work_id = js(f"""
(function() {{
    var cards = document.querySelectorAll('[class*="assetItemWrapper"]');
    for(var i=0; i<cards.length; i++) {{
        if(cards[i].textContent.includes('{song}')) {{
            var wid = cards[i].getAttribute('data-work-id') || '';
            return 'work_id=' + wid;
        }}
    }}
    return 'not-found';
}})();
""")
print(f"work-id: {work_id}", flush=True)

wid = work_id.replace('work_id=', '').strip() if work_id and 'work_id=' in str(work_id) else ''
if not wid:
    print("❌ 未找到work-id", flush=True)
    sys.exit(1)

# ── 2. CDP: cleanup弹窗 → 创建新页面 → 导航到发布URL ──
import requests, websocket

# 获取Browser WS
ver = requests.get('http://localhost:9223/json/version', timeout=5).json()
bws = ver['webSocketDebuggerUrl']

b_ws = websocket.create_connection(bws, timeout=10)

# 关闭旧的complete-publish页（如果有）
b_ws.send(json.dumps({'id':1, 'method':'Target.getTargets', 'params':{}}))
resp = json.loads(b_ws.recv())
for t in resp.get('result',{}).get('targetInfos',[]):
    if 'complete-publish' in t.get('url',''):
        b_ws.send(json.dumps({'id':2, 'method':'Target.closeTarget', 'params':{'targetId':t['targetId']}}))
        json.loads(b_ws.recv())
        print("  清理旧发布页✅", flush=True)

# 创建新页面
b_ws.send(json.dumps({'id':3, 'method':'Target.createTarget', 'params':{'url':'about:blank'}}))
resp = json.loads(b_ws.recv())
new_tid = resp.get('result',{}).get('targetId','')
b_ws.close()

publish_url = f"https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId={wid}"
print(f"发布URL: {publish_url[:80]}", flush=True)

# 连接新页面CDP
pw = websocket.create_connection(f'ws://localhost:9223/devtools/page/{new_tid}', timeout=10)
def cdp(method, params=None):
    if params is None: params = {}
    pw.send(json.dumps({'id':1, 'method':method, 'params':params}))
    return json.loads(pw.recv())

# 导航
cdp('Page.enable')
cdp('Page.navigate', {'url': publish_url})
time.sleep(5)
# 禁用弹窗
cdp('Runtime.evaluate', {
    'expression': 'window.onbeforeunload=null;',
    'returnByValue': True
})
print("1. 进入发布页✅", flush=True)

# ── 3. 智能封面 ──
print("2. 智能封面...", flush=True)

# 点智能封面
cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '智能封面') {
                all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(3)

# 一键生成封面
cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
                all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(4)

# 使用封面
cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '使用封面') {
                all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                return 'used';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(2)
print("   封面✅", flush=True)

# 检查页面文本
page_text = cdp('Runtime.evaluate', {
    'expression': 'document.body.textContent',
    'returnByValue': True
}).get('result',{}).get('result',{}).get('value','')
print(f"   文本长度: {len(page_text)}", flush=True)

# ── 4. 第一次「下一步」 ──
print("3. 第一次下一步...", flush=True)
cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        window.scrollTo(0, document.body.scrollHeight);
        return 'scrolled';
    })();
    ''',
    'returnByValue': True
})
time.sleep(1)

cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('button');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent.trim() === '下一步') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                ['mousedown','mouseup','click'].forEach(function(t) {
                    all[i].dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window, button:0}));
                });
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(4)

page_text2 = cdp('Runtime.evaluate', {
    'expression': 'document.body.textContent',
    'returnByValue': True
}).get('result',{}).get('result',{}).get('value','')
print(f"   文本长度: {len(page_text2)}", flush=True)

# ── 5. 艺人信息 ──
print("4. 艺人信息...", flush=True)
cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '有主页链接') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(2)

cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('*');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent && all[i].textContent.trim() === '无主页链接') {
                all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(1)
print("   艺人信息✅", flush=True)

# ── 6. 第二次「下一步」 ──
print("5. 第二次下一步...", flush=True)
cdp('Runtime.evaluate', {
    'expression': '''
    (function() {
        var all = document.querySelectorAll('button');
        for(var i=0; i<all.length; i++) {
            if(all[i].textContent.trim() === '下一步') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                ['mousedown','mouseup','click'].forEach(function(t) {
                    all[i].dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window, button:0}));
                });
                return 'clicked';
            }
        }
        return 'not-found';
    })();
    ''',
    'returnByValue': True
})
time.sleep(5)

# 检查是否出现了letsign标签页
b_ws2 = websocket.create_connection(bws, timeout=5)
b_ws2.send(json.dumps({'id':1, 'method':'Target.getTargets', 'params':{}}))
resp2 = json.loads(b_ws2.recv())
b_ws2.close()

letsign_tid = None
letsign_url = ""
for t in resp2.get('result',{}).get('targetInfos',[]):
    if 'letsign' in t.get('url','') and t['type'] == 'page':
        letsign_tid = t['targetId']
        letsign_url = t['url']
        break

if letsign_tid:
    print(f"6. 进入letsign: {letsign_url[:60]}...", flush=True)
    
    # 连接letsign页CDP
    lw = websocket.create_connection(f'ws://localhost:9223/devtools/page/{letsign_tid}', timeout=10)
    def l_cdp(method, params=None):
        if params is None: params = {}
        lw.send(json.dumps({'id':1, 'method':method, 'params':params}))
        return json.loads(lw.recv())
    
    # 点批量签署
    l_cdp('Runtime.evaluate', {
        'expression': '''
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
        ''',
        'returnByValue': True
    })
    time.sleep(3)
    
    # 检查验证码区域
    l_text = l_cdp('Runtime.evaluate', {
        'expression': 'document.body.textContent',
        'returnByValue': True
    }).get('result',{}).get('result',{}).get('value','')
    
    if '验证码' in l_text or '验证码' in l_text:
        print("\n⚠️ 需要验证码！", flush=True)
        
        if verify_code:
            # 有验证码，填入
            l_cdp('Runtime.evaluate', {
                'expression': f'''
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
                ''',
                'returnByValue': True
            })
            time.sleep(1)
            
            # 点确定
            l_cdp('Runtime.evaluate', {
                'expression': '''
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
                ''',
                'returnByValue': True
            })
            time.sleep(4)
            
            # 验证
            result_t = l_cdp('Runtime.evaluate', {
                'expression': 'document.body.textContent.includes("签署成功")',
                'returnByValue': True
            }).get('result',{}).get('result',{}).get('value', False)
            
            if result_t:
                print("✅ 签署成功！", flush=True)
            else:
                # 检查状态
                final_t = l_cdp('Runtime.evaluate', {
                    'expression': 'document.body.textContent.substring(0, 500)',
                    'returnByValue': True
                }).get('result',{}).get('result',{}).get('value','')
                print(f"签署状态: {final_t[:100]}", flush=True)
        else:
            # 点获取验证码
            l_cdp('Runtime.evaluate', {
                'expression': '''
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
                ''',
                'returnByValue': True
            })
            print("   获取验证码已点击，等待验证码...", flush=True)
            # 保存状态供下次使用
            import os
            with open('/tmp/publish_state.json', 'w') as f:
                json.dump({'song': song, 'letsign_tid': letsign_tid, 'wid': wid}, f)
            print(f"\n>>> 陛下，请在手机上查看验证码，然后告诉我 <<<", flush=True)
        
        lw.close()
    else:
        print(f"   letsign页面状态: {l_text[:100]}", flush=True)
        lw.close()
else:
    print("❌ 未找到letsign标签页", flush=True)
    # 检查当前页面有没有letsign弹窗
    pw_text = cdp('Runtime.evaluate', {
        'expression': 'document.body.textContent',
        'returnByValue': True
    }).get('result',{}).get('result',{}).get('value','')
    print(f"当前页文本: {pw_text[:200]}", flush=True)

pw.close()
print(f"\n=== 发布 {song} 阶段完成 ===", flush=True)
