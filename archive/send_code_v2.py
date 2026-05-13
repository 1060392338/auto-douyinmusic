"""连接新Chrome并发送验证码"""
import time, sys
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
print("✅ 已连接", flush=True)
time.sleep(2)

# 检查当前页面 - 应该已经是 studio 页
body = P.ele('tag:body').text
print(f"文本长度: {len(body)}", flush=True)
print(f"前200字: {body[:200]}", flush=True)

if 'AI 作曲' in body or 'AI 作词' in body:
    print("✅ 会话有效，已登录！", flush=True)
else:
    print("❌ 需要登录", flush=True)
    
    # 点击登录
    for btn in P.eles('tag:button'):
        t = (btn.text or '').strip()
        if t == '登录':
            btn.click()
            time.sleep(3)
            print("点了登录按钮", flush=True)
            break
    
    body2 = P.ele('tag:body').text
    
    # 切到验证码标签
    if '验证码登录' in body2:
        for span in P.eles('tag:span'):
            if span.text.strip() == '验证码登录':
                span.click()
                time.sleep(2)
                break
    
    body3 = P.ele('tag:body').text
    
    # 输入手机号
    inp = P.ele('css:input[placeholder="请输入手机号"]', timeout=3)
    if inp:
        inp.input('17620417470')
        time.sleep(1)
        print("✅ 已输入手机号", flush=True)
        
        # 点击获取验证码
        get_btn = P.ele('xpath://span[contains(text(),"获取")]', timeout=3)
        if get_btn:
            get_btn.click()
            print("✅ 已点击获取验证码，请查收短信！", flush=True)
        else:
            # 用 JS 找
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
            print("✅ 已点击获取验证码（JS）", flush=True)

print("\n✅ 完成", flush=True)
