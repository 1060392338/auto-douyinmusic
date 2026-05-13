"""方案A v2: 确保封面弹窗关闭后再点下一步"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 禁用弹窗 + 导航
P.run_js("window.onbeforeunload=null;")
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)
P.run_js("window.onbeforeunload=null;")

# 等页面加载
body = None
for _ in range(5):
    time.sleep(2)
    try:
        body = P.ele('tag:body', timeout=5)
        if body and len(body.text) > 200:
            break
    except:
        P.run_js("window.onbeforeunload=null;")

if not body or len(body.text) < 200:
    print("❌ 加载失败", flush=True)
    exit()

text = body.text
print(f"✅ 发布页, 文本长度:{len(text)}", flush=True)

# 智能封面 - 使用可靠的方式
print("1. 点击智能封面...", flush=True)
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

t2 = P.ele('tag:body', timeout=5).text
if '一键生成' in t2:
    print("2. 一键生成封面...", flush=True)
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
        print("3. 使用封面...", flush=True)
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
        print("4. 等待弹窗关闭...", flush=True)
        
        # 检查弹窗是否还开着，如果还在就点取消
        t4 = P.ele('tag:body', timeout=5).text
        if '使用封面' in t4 and '取消' in t4:
            print("   弹窗还未关闭，点取消...", flush=True)
            P.run_js("""
            window.onbeforeunload=null;
            document.querySelectorAll('*').forEach(function(el) {
                if (el.textContent && el.textContent.trim() === '取消') {
                    el.click();
                }
                if (el.textContent && el.textContent.trim() === '关闭') {
                    el.click();
                }
            });
            """)
            time.sleep(3)
        
        print("   ✅ 封面处理完成", flush=True)

# 5. 艺人信息（如果有）
P.run_js("window.onbeforeunload=null;")
try:
    t5 = P.ele('tag:body', timeout=5).text
    if '有主页链接' in t5:
        print("5. 艺人信息...", flush=True)
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
except:
    pass

# 6. 关键：先关闭所有可能打开的弹窗/模态框，再点下一步
print("6. 关闭所有弹窗...", flush=True)
P.run_js("""
window.onbeforeunload=null;
// 尝试关闭任何打开的 dialog/modal
var closeBtns = document.querySelectorAll('[class*="close"], [class*="Close"], [class*="cancel"], [class*="Cancel"]');
closeBtns.forEach(function(btn) {
    if (btn.offsetParent !== null) {  // 只点击可见的
        btn.click();
    }
});
// 点击 取消/关闭
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if ((t === '取消' || t === '关闭' || t === 'X') && el.offsetParent !== null) {
        el.click();
    }
});
""")
time.sleep(2)

# 7. 滚动到页面底部，找下一步按钮
print("7. 滚动到底部...", flush=True)
P.run_js("window.onbeforeunload=null;window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# 8. 点击下一步
print("8. 点击下一步...", flush=True)
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if (t === '下一步' && el.offsetParent !== null) {
        el.scrollIntoView({behavior:'instant',block:'center'});
        el.focus();
        ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {
            el.dispatchEvent(new PointerEvent(ev, {bubbles:true, cancelable:true}));
        });
    }
});
""")
time.sleep(8)

# 9. 检查结果
print(f"   URL: {P.url[:80]}", flush=True)
pages = requests.get('http://localhost:9223/json').json()
print("\n9. 页面:", flush=True)
for p in pages:
    url = p.get('url', '')
    print(f"   {p['title'][:30]} | {url[:80]}", flush=True)
    if 'letsign' in url:
        print(f"   ✅ 合同页!", flush=True)

try:
    t6 = P.ele('tag:body', timeout=5).text
    print(f"\n底部600: ...{[t6[-600:]]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','合同签署','签署协议']:
        if kw in t6:
            print(f"   ✅ {kw}", flush=True)
except:
    pass

print("\n✅ 完成", flush=True)
