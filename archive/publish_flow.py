"""登录 -> 进入发布流程（验证码通过参数传入）"""
import time, json, requests, sys
from DrissionPage import ChromiumPage

# 验证码通过命令行参数传入
VERIFY_CODE = sys.argv[1] if len(sys.argv) > 1 else None

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 导航到 studio
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(6)

body = P.ele('tag:body').text
print(f"Studio页长度: {len(body)}", flush=True)

if 'AI 作曲' in body or 'AI 作词' in body:
    print("✅ 已登录！跳过登录", flush=True)
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
        print("已点击获取验证码", flush=True)
        
        if VERIFY_CODE:
            time.sleep(2)
            code_inp = P.ele('css:input[placeholder="请输入验证码"]', timeout=3)
            if code_inp:
                code_inp.input(VERIFY_CODE)
                time.sleep(1)
                print("已输入验证码", flush=True)
                
                # 登录按钮
                P.run_js("""
                (function() {
                    var btn = document.querySelector('#douyin_login_comp_btn_id');
                    if (btn) { btn.click(); return; }
                    var all = document.querySelectorAll('*');
                    for (var i = 0; i < all.length; i++) {
                        if (all[i].textContent && all[i].textContent.trim() === '登录' && all[i].id) {
                            all[i].click(); return;
                        }
                    }
                })();
                """)
                time.sleep(4)
                print("已点击登录", flush=True)
        else:
            print("未提供验证码参数", flush=True)

# 验证登录后导航到发布页
body = P.ele('tag:body').text
if 'AI 作曲' in body or 'AI 作词' in body or '下一步' in body:
    print("✅ 登录成功！", flush=True)
else:
    print("⚠️ 登录可能未成功，继续尝试...", flush=True)

# 导航到发布页
print("导航到发布页...", flush=True)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(8)

body = P.ele('tag:body').text
print(f"发布页长度: {len(body)}", flush=True)
print(body[:500], flush=True)

if '下一步' in body and '蝉声漫旧夏' in body:
    print("✅ 在发布页！", flush=True)
    
    # 处理艺人信息 - 有主页链接 -> 无主页链接
    if '有主页链接' in body:
        print("切换艺人信息: 有主页链接 -> 无主页链接", flush=True)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '有主页链接') {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].focus();
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(2)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '无主页链接') {
                    all[i].focus();
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(2)
    
    # 智能封面
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
    
    body2 = P.ele('tag:body').text
    if '一键生成' in body2:
        print("点击一键生成封面...", flush=True)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(5)
        
        body3 = P.ele('tag:body').text
        if '使用封面' in body3:
            print("点击使用封面...", flush=True)
            P.run_js("""
            (function() {
                var all = document.querySelectorAll('*');
                for (var i = 0; i < all.length; i++) {
                    if (all[i].textContent && all[i].textContent.trim() === '使用封面') {
                        all[i].scrollIntoView({behavior:'instant', block:'center'});
                        all[i].click();
                        return;
                    }
                }
            })();
            """)
            time.sleep(3)
            print("✅ 封面已设置", flush=True)
    
    # 点击下一步
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
    
    # 检查新页面
    pages = requests.get('http://localhost:9223/json').json()
    for p in pages:
        url = p.get('url', '')
        if 'letsign' in url or 'summon' in url:
            print(f"✅ 发现合同页面: {p['title'][:30]} | {url[:100]}", flush=True)
            # 保存 ws url
            WS_URL = p['webSocketDebuggerUrl']
            print(f"WS: {WS_URL}", flush=True)
    
    body4 = P.ele('tag:body').text
    print(f"\n最终页面 (前2000):", flush=True)
    print(body4[:2000], flush=True)
    
    # 检查发布页URL是否变化
    final_url = P.url
    print(f"\n最终URL: {final_url[:100]}", flush=True)
else:
    print("❌ 不在发布页", flush=True)
