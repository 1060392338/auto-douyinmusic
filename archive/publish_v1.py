#!/usr/bin/env python3
"""
发布 v1 - 逐首发行全曲
用法: python3 publish_v1.py <歌名> [验证码]

不带验证码: 走完表单到签署页，等待提供验证码
带验证码: 走完整流程（含签署）
"""
import sys, time, os, signal
from DrissionPage import ChromiumPage

def _cleanup(signum, frame):
    print("\n⚠️ 清理中...", flush=True)
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

P = ChromiumPage(addr_or_opts="127.0.0.1:9223")

def js(code):
    for _ in range(3):
        try:
            return P.run_js(code)
        except:
            try: P.handle_alert(accept=True)
            except: pass
            time.sleep(1)
    return None

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
verify_code = sys.argv[2] if len(sys.argv) > 2 else ""

print(f"=== 发布 {song} ===\n", flush=True)

# ── 1. 导航到资产页 ──
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
time.sleep(6)

# ── 2. 找"发行全曲"点进去 ──
js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '发行全曲') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return;
        }
    }
})();
""")
print("1. 点击发行全曲✅", flush=True)
time.sleep(5)

# 检查是否跳转到发布页
url = P.url
if 'complete-publish' not in url:
    # 可能点了错误的，重试
    print(f"   URL: {url[:60]}, 等待跳转...", flush=True)
    time.sleep(8)
    url = P.url
    if 'complete-publish' not in url:
        print(f"❌ 未跳转到发行页: {url[:60]}", flush=True)

# 禁用弹窗
js("window.onbeforeunload=null;")
time.sleep(1)

# ── 3. 智能封面 ──
print("2. 智能封面...", flush=True)
js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '智能封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(3)

# 一键生成封面
js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'clicked';
        }
    }
    return 'not-found';
})();
""")
time.sleep(4)

# 使用封面
js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '使用封面') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return 'used';
        }
    }
    return 'not-found';
})();
""")
time.sleep(3)
print("   封面✅", flush=True)

# ── 4. 第一次「下一步」 ──
print("3. 第一次下一步...", flush=True)
js("""
window.scrollTo(0, document.body.scrollHeight);
setTimeout(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '下一步' && all[i].tagName === 'BUTTON') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return;
        }
    }
}, 500);
""")
time.sleep(4)
print("   下一步1✅", flush=True)

# ── 5. 艺人信息：有主页链接 → 无主页链接 ──
print("4. 艺人信息...", flush=True)
js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '有主页链接') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return;
        }
    }
})();
""")
time.sleep(2)

js("""
(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '无主页链接') {
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return;
        }
    }
})();
""")
time.sleep(1)
print("   艺人信息✅", flush=True)

# ── 6. 第二次「下一步」 ──
print("5. 第二次下一步...", flush=True)
js("""
window.scrollTo(0, document.body.scrollHeight);
setTimeout(function() {
    var all = document.querySelectorAll('*');
    for(var i=0; i<all.length; i++) {
        if(all[i].textContent && all[i].textContent.trim() === '下一步' && all[i].tagName === 'BUTTON') {
            all[i].scrollIntoView({behavior:'instant', block:'center'});
            all[i].dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window, button:0}));
            return;
        }
    }
}, 500);
""")
time.sleep(4)
print("   下一步2✅", flush=True)

# ── 7. 合同签署 ──
print("\n6. 进入签署...", flush=True)

# 找letsign标签页
targets_raw = js("JSON.stringify(await new Promise(r => P.run_cdp ? null : null))")
# 用CDP查找letsign
import json
try:
    import requests
    ver = requests.get('http://localhost:9223/json/version', timeout=5).json()
    bws = ver['webSocketDebuggerUrl']
    
    import websocket
    ws = websocket.create_connection(bws, timeout=5)
    ws.send(json.dumps({'id': 1, 'method': 'Target.getTargets', 'params': {}}))
    resp = json.loads(ws.recv())
    
    letsign_tid = None
    for t in resp.get('result', {}).get('targetInfos', []):
        if 'letsign' in t.get('url', '') and t['type'] == 'page':
            letsign_tid = t['targetId']
            print(f"   找到letsign标签页: {t['url'][:60]}", flush=True)
            break
    
    ws.close()
    
    if letsign_tid:
        # 切换到letsign标签页
        js(f"window.location.href='';")  # dummy
        # 用CDP直接操作letsign页
        ws2 = websocket.create_connection(f'ws://localhost:9223/devtools/page/{letsign_tid}', timeout=10)
        
        def cdp(method, params=None):
            if params is None: params = {}
            ws2.send(json.dumps({'id': 1, 'method': method, 'params': params}))
            return json.loads(ws2.recv())
        
        # 检查是否已签署（批量签署按钮）
        body_text = cdp('Runtime.evaluate', {
            'expression': 'document.body.textContent',
            'returnByValue': True
        }).get('result', {}).get('result', {}).get('value', '')
        
        if '批量签署' in body_text:
            print("   找到批量签署按钮", flush=True)
            cdp('Runtime.evaluate', {
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
        
        # 检查是否需要验证码
        body_text2 = cdp('Runtime.evaluate', {
            'expression': 'document.body.textContent',
            'returnByValue': True
        }).get('result', {}).get('result', {}).get('value', '')
        
        if verify_code:
            # 直接填验证码
            print(f"   填入验证码: {verify_code}", flush=True)
            cdp('Runtime.evaluate', {
                'expression': f'''
                (function() {{
                    var inputs = document.querySelectorAll('input');
                    for(var i=0; i<inputs.length; i++) {{
                        if(inputs[i].placeholder && inputs[i].placeholder.includes('验证码')) {{
                            inputs[i].focus();
                            inputs[i].value = "{verify_code}";
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
            cdp('Runtime.evaluate', {
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
            time.sleep(3)
            
            # 验证签署
            result_text = cdp('Runtime.evaluate', {
                'expression': 'document.body.textContent',
                'returnByValue': True
            }).get('result', {}).get('result', {}).get('value', '')
            
            if '签署成功' in result_text:
                print("✅ 签署成功！", flush=True)
            else:
                print(f"⚠️ 签署状态: {result_text[:200]}", flush=True)
        else:
            print("\n⚠️ 需要验证码！", flush=True)
            # 聚焦输入框
            cdp('Runtime.evaluate', {
                'expression': '''
                (function() {
                    var inputs = document.querySelectorAll('input');
                    for(var i=0; i<inputs.length; i++) {
                        if(inputs[i].placeholder && inputs[i].placeholder.includes('验证码')) {
                            inputs[i].focus();
                            inputs[i].click();
                            return 'focused';
                        }
                    }
                    return JSON.stringify(inputs.length + ' inputs');
                })();
                ''',
                'returnByValue': True
            })
            time.sleep(1)
            
            # 点获取验证码
            cdp('Runtime.evaluate', {
                'expression': '''
                (function() {
                    var all = document.querySelectorAll('*');
                    for(var i=0; i<all.length; i++) {
                        var t = all[i].textContent;
                        if(t && t.trim() === '获取验证码') {
                            all[i].scrollIntoView({behavior:'instant', block:'center'});
                            ['mousedown','mouseup','click'].forEach(function(ev) {
                                all[i].dispatchEvent(new MouseEvent(ev, {bubbles:true, cancelable:true, view:window, button:0}));
                            });
                            return 'clicked';
                        }
                    }
                    return 'not-found';
                })();
                ''',
                'returnByValue': True
            })
            print("   验证码已发送到手机，请提供", flush=True)
        
        ws2.close()
    else:
        print("❌ 未找到letsign标签页", flush=True)
        
except Exception as e:
    print(f"⚠️ 签署异常: {e}", flush=True)

# ── 8. 返回资产页验证 ──
time.sleep(3)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
time.sleep(6)

body = P.ele("tag:body").text
if song in body:
    idx = body.find(song)
    snippet = body[idx:idx+100]
    if '查看详情' in snippet:
        print(f"\n✅ {song} 发布成功！状态: 查看详情", flush=True)
    else:
        print(f"\n{song} 在资产页，但状态: {snippet[:50]}", flush=True)
else:
    print(f"\n❌ {song} 发布可能失败", flush=True)

print("\n=== 完成 ===", flush=True)
