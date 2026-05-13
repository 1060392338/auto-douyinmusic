"""方案A：导航前禁用弹窗 + 完整发布流程"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# === 关键：先禁用弹窗，再导航 ===
print("1. 禁用弹窗...", flush=True)
P.run_js("window.onbeforeunload = null;")
time.sleep(1)

# 导航到发布页（用 JS location，不经过弹窗）
print("2. 导航到发布页...", flush=True)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)

# 导航后再禁用一次
P.run_js("window.onbeforeunload = null;")

# 等待页面加载
body = None
for _ in range(5):
    time.sleep(2)
    try:
        body = P.ele('tag:body', timeout=5)
        if body and len(body.text) > 200:
            break
    except:
        P.run_js("window.onbeforeunload = null;")  # 再试一次

if not body or len(body.text) < 200:
    print("❌ 页面加载失败", flush=True)
    # 查看当前URL
    print(f"URL: {P.url[:100]}", flush=True)
    exit()

text = body.text
print(f"✅ 发布页加载, 文本长度:{len(text)}", flush=True)

# 3. 艺人信息
if '有主页链接' in text:
    print("3. 艺人信息: 有主页链接 -> 无主页链接", flush=True)
    P.run_js("""
    window.onbeforeunload=null;
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '有主页链接') {
            el.scrollIntoView({behavior:'instant',block:'center'});
            el.focus(); el.click();
        }
    });
    """)
    time.sleep(2)
    P.run_js("""
    document.querySelectorAll('*').forEach(function(el) {
        var t = (el.textContent || '').trim();
        if (t === '无主页链接') {
            el.focus(); el.click();
        }
    });
    """)
    time.sleep(2)
    print("   ✅ 无主页链接", flush=True)

# 4. 智能封面
print("4. 智能封面...", flush=True)
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '智能封面') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
""")
time.sleep(3)

try:
    t2 = P.ele('tag:body', timeout=5).text
    if '一键生成' in t2:
        print("   ✅ 一键生成封面...", flush=True)
        P.run_js("""
        window.onbeforeunload=null;
        document.querySelectorAll('*').forEach(function(el) {
            if (el.textContent && el.textContent.trim() === '一键生成封面') {
                el.scrollIntoView({behavior:'instant',block:'center'});
                el.click();
            }
        });
        """)
        time.sleep(5)
        
        t3 = P.ele('tag:body', timeout=5).text
        if '使用封面' in t3:
            print("   ✅ 使用封面...", flush=True)
            P.run_js("""
            window.onbeforeunload=null;
            document.querySelectorAll('*').forEach(function(el) {
                if (el.textContent && el.textContent.trim() === '使用封面') {
                    el.scrollIntoView({behavior:'instant',block:'center'});
                    el.click();
                }
            });
            """)
            time.sleep(3)
            print("   ✅ 封面已设置！", flush=True)
except:
    print("   ⚠️ 智能封面跳过", flush=True)

# 5. 点击下一步
print("5. 点击下一步...", flush=True)
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '下一步') {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
""")
time.sleep(8)

print(f"   URL: {P.url[:80]}", flush=True)

# 6. 检查所有页面
print("\n6. 检查页面:", flush=True)
pages = requests.get('http://localhost:9223/json').json()
for p in pages:
    url = p.get('url', '')
    print(f"   {p['title'][:30]} | {url[:80]}", flush=True)
    if 'letsign' in url:
        print(f"   ✅ 合同页! WS:{p['webSocketDebuggerUrl'][:60]}", flush=True)

try:
    t4 = P.ele('tag:body', timeout=5).text
    print(f"\n底部500字: ...{t4[-500:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','合同签署','授权信息']:
        if kw in t4:
            print(f"   ✅ {kw}", flush=True)
except:
    pass

print("\n✅ 流程完成", flush=True)
