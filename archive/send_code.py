"""登录流程 - 触发验证码"""
import time, sys
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(3)

# 处理弹窗
for _ in range(3):
    try:
        P.run_cdp('Page.handleJavaScriptDialog', accept=True)
        time.sleep(0.5)
    except:
        pass

# 导航
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio';")
time.sleep(8)

# 获取 body - 带重试
body = None
for _ in range(3):
    try:
        body = P.ele('tag:body', timeout=5)
        break
    except:
        time.sleep(2)

if not body:
    print("❌ 无法获取页面", flush=True)
    sys.exit(1)

text = body.text
print(f"文本长度: {len(text)}", flush=True)
print(f"前100字: {text[:100]}", flush=True)

if 'AI 作词' in text or 'AI 作曲' in text:
    print("✅ 已登录", flush=True)
else:
    # 点击登录
    for el in P.eles('tag:button'):
        if '登录' in (el.text or ''):
            el.click()
            time.sleep(3)
            print("已点登录按钮", flush=True)
            break
    else:
        # 用 JS 找
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var t = all[i].textContent || '';
                if (t.trim() === '登录' && (all[i].tagName === 'BUTTON' || all[i].id)) {
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(3)
    
    text2 = P.ele('tag:body').text
    if '验证码登录' in text2:
        # 切到验证码
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
            print("✅ 已输入手机号17620417470", flush=True)
            
            # 获取验证码
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
            print("✅ 已点击获取验证码，请查收短信", flush=True)
