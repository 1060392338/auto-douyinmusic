"""完整发布流程 - 蝉声漫旧夏"""
import time, json, requests, sys
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 1. 导航到发布页
print("1. 导航到发布页...", flush=True)
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(8)

body = P.ele('tag:body').text
print(f"   长度: {len(body)}", flush=True)

if '下一步' not in body:
    print("❌ 发布页加载失败", flush=True)
    sys.exit(1)
print("✅ 在发布页", flush=True)

# 2. 艺人信息补充 - 有主页链接 -> 无主页链接
if '有主页链接' in body:
    print("2. 艺人信息: 有主页链接->无主页链接", flush=True)
    P.run_js("""
    (function() {
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent && all[i].textContent.trim() === '有主页链接') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                all[i].focus(); all[i].click(); return;
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
                all[i].focus(); all[i].click(); return;
            }
        }
    })();
    """)
    time.sleep(2)
    print("   ✅ 已设置无主页链接", flush=True)

# 3. 智能封面
print("3. 智能封面...", flush=True)
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
    print("  点击一键生成封面...", flush=True)
    P.run_js("""
    (function() {
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            if (all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
                all[i].scrollIntoView({behavior:'instant', block:'center'});
                all[i].click(); return;
            }
        }
    })();
    """)
    time.sleep(5)
    
    body3 = P.ele('tag:body').text
    if '使用封面' in body3:
        print("  点击使用封面...", flush=True)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '使用封面') {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].click(); return;
                }
            }
        })();
        """)
        time.sleep(3)
        print("   ✅ 封面已设置", flush=True)
    else:
        print("   ⚠️ 封面未生成", flush=True)
else:
    print("   ⚠️ 智能封面弹窗未弹出", flush=True)

# 4. 点击下一步 -> 签署协议
print("4. 点击下一步...", flush=True)
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

# 5. 检查合同页面
pages = requests.get('http://localhost:9223/json').json()
print(f"5. 检查新页面...", flush=True)
for p in pages:
    url = p.get('url', '')
    if 'letsign' in url:
        print(f"   ✅ 发现合同页: {url[:100]}", flush=True)
        contract_ws = p['webSocketDebuggerUrl']
        print(f"   WS: {contract_ws}", flush=True)

body4 = P.ele('tag:body').text
print(f"\n当前页面 (前500):", flush=True)
print(body4[:500], flush=True)

# 检测关键文本
for kw in ['签署', '合同', '协议', '批量签署', 'letsign', '意愿认证']:
    if kw in body4:
        print(f"   ✅ 关键词: {kw}", flush=True)
