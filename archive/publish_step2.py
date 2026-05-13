"""发布 Step 2: 生成封面 + 点击下一步"""
import time, json, requests
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 确保在发布页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)
try:
    P.run_cdp('Page.handleJavaScriptDialog', accept=True)
except:
    pass

print("1. 点击「智能封面」", flush=True)
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
            return 'clicked';
        }
    }
    return 'not_found';
})();
""")
time.sleep(3)

body = P.ele('tag:body').text
print(f"点击智能封面后文本含'一键生成': {'一键生成' in body}", flush=True)
print(f"含'使用封面': {'使用封面' in body}", flush=True)
print(f"含'封面预览': {'封面预览' in body}", flush=True)
print(body[:1000], flush=True)

# 如果弹出了封面生成弹窗
if '一键生成' in body or '封面预览' in body:
    print("\n2. 点击「一键生成封面」", flush=True)
    for kw in ['一键生成', '生成封面', '开始生成']:
        P.run_js(f"""
        (function() {{
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {{
                if (all[i].textContent && all[i].textContent.trim() === '{kw}') {{
                    all[i].scrollIntoView({{behavior:'instant', block:'center'}});
                    all[i].focus();
                    ['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(ev) {{
                        all[i].dispatchEvent(new PointerEvent(ev, {{bubbles:true, cancelable:true}}));
                    }});
                    return;
                }}
            }}
        }})();
        """)
        time.sleep(2)
    
    # 检查是否生成了封面
    body2 = P.ele('tag:body').text
    if '使用封面' in body2:
        print("\n3. ✅ 封面已生成！点击「使用封面」", flush=True)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '使用封面') {
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
    
    # 关闭弹窗
    body3 = P.ele('tag:body').text
    if '一键生成' in body3 or '使用封面' in body3:
        print("弹窗还在，尝试关闭...", flush=True)
        for kw in ['取消', '关闭', 'X']:
            P.run_js(f"""
            (function() {{
                var all = document.querySelectorAll('*');
                for (var i = 0; i < all.length; i++) {{
                    if (all[i].textContent && all[i].textContent.trim() === '{kw}') {{
                        all[i].click();
                        return;
                    }}
                }}
            }})();
            """)
            time.sleep(1)

# 4. 点击「下一步」
print("\n4. 点击「下一步」", flush=True)
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
            return 'clicked_next';
        }
    }
    return 'no_next_button';
})();
""")
time.sleep(5)

body4 = P.ele('tag:body').text
print(f"点击下一步后URL: {P.url}", flush=True)
print(f"页面文本 (前1500):", flush=True)
print(body4[:1500], flush=True)

# 检查是否进入了合同签署
if '签署' in body4 or '合同' in body4 or '协议' in body4 or 'letsign' in P.url or 'summon' in P.url:
    print("\n✅ 进入了签约/合同页面!", flush=True)
elif '下一步' in body4:
    print("\n⏳ 还在当前页面，可能下一步没生效", flush=True)
else:
    print("\n❓ 页面状态不明", flush=True)
