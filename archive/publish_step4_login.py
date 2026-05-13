"""验证码登录后进入发布页"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 导航到 studio 页触发生成弹窗
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(6)

body = P.ele('tag:body').text
print(f"Studio页长度: {len(body)}", flush=True)

if 'AI 作曲' in body or 'AI 作词' in body:
    print("✅ 已登录！直接去发布页", flush=True)
else:
    print("❌ 需要登录", flush=True)
    
    # 点击登录按钮
    P.run_js("""
    (function() {
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent && all[i].textContent.trim() === '登录') {
                all[i].click();
                return;
            }
        }
    })();
    """)
    time.sleep(3)
    
    body2 = P.ele('tag:body').text
    print(f"点击登录后: 含验证码登录={'验证码登录' in body2}", flush=True)
    
    if '验证码登录' in body2:
        # 切到验证码登录
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '验证码登录') {
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(2)
        
        # 输入手机号
        inp = P.ele('css:input[placeholder="请输入手机号"]', timeout=3)
        if inp:
            inp.input('17620417470')
            time.sleep(1)
            print("已输入手机号", flush=True)
            
            # 点击获取验证码
            P.run_js("""
            (function() {
                var all = document.querySelectorAll('*');
                for (var i = 0; i < all.length; i++) {
                    if (all[i].textContent && all[i].textContent.indexOf('获取') >= 0) {
                        all[i].click();
                        return;
                    }
                }
            })();
            """)
            print("已点击获取验证码，请查收手机短信", flush=True)
            
            # 等待用户输入验证码
            code = input("请输入验证码: ")
            
            # 输入验证码
            code_inp = P.ele('css:input[placeholder="请输入验证码"]', timeout=3)
            if code_inp:
                code_inp.input(code)
                time.sleep(1)
                
                # 点击登录按钮
                P.run_js("""
                (function() {
                    var btn = document.querySelector('#douyin_login_comp_btn_id');
                    if (btn) {
                        btn.click();
                    } else {
                        var all = document.querySelectorAll('*');
                        for (var i = 0; i < all.length; i++) {
                            if (all[i].textContent && all[i].textContent.trim() === '登录' && all[i].tagName !== 'A') {
                                if (all[i].querySelector('*[class*="login"]') || all[i].id.includes('login')) {
                                    all[i].click();
                                    return;
                                }
                            }
                        }
                    }
                })();
                """)
                time.sleep(3)
                print("点击登录", flush=True)

# 登录后导航到发布页
print("\n导航到发布页...", flush=True)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(8)

body3 = P.ele('tag:body').text
print(f"发布页长度: {len(body3)}", flush=True)
if '下一步' in body3 and '蝉声漫旧夏' in body3:
    print("✅ 已进入发布页！", flush=True)
    # 继续流程 - 智能封面
    print("处理智能封面...", flush=True)
    P.run_js("""
    (function() {
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent && all[i].textContent.trim() === '智能封面') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                all[i].focus();
                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                    all[i].dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
                });
                return;
            }
        }
    })();
    """)
    time.sleep(3)
    
    body4 = P.ele('tag:body').text
    if '一键生成' in body4:
        print("点击一键生成封面...", flush=True)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(5)
        
        body5 = P.ele('tag:body').text
        if '使用封面' in body5:
            print("点击使用封面...", flush=True)
            P.run_js("""
            (function() {
                var all = document.querySelectorAll('*');
                for (var i = 0; i < all.length; i++) {
                    if (all[i].textContent && all[i].textContent.trim() === '使用封面') {
                        all[i].click();
                        return;
                    }
                }
            })();
            """)
            time.sleep(3)
    
    # 点击下一步到合同
    print("点击下一步...", flush=True)
    P.run_js("""
    (function() {
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent && all[i].textContent.trim() === '下一步') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                all[i].focus();
                ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
                    all[i].dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
                });
                return;
            }
        }
    })();
    """)
    time.sleep(8)
    
    # 检查是否有新的合同页面
    pages = requests.get('http://localhost:9223/json').json()
    for p in pages:
        url = p.get('url', '')
        if 'letsign' in url or 'summon' in url or 'sign' in url.lower():
            print(f"✅ 发现合同页面: {url[:100]}", flush=True)
    
    body6 = P.ele('tag:body').text
    print(f"最终页面 (前1000):", flush=True)
    print(body6[:1000], flush=True)
else:
    print("❌ 进入发布页失败", flush=True)
    print(body3[:500], flush=True)
