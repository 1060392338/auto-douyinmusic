"""发布 Step 3: 智能封面 + 下一步到合同签署"""
import time
from DrissionPage import ChromiumPage

P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)
try:
    P.run_cdp('Page.handleJavaScriptDialog', accept=True)
except:
    pass

body = P.ele('tag:body').text

# 检查当前在哪个步骤
print("=== 当前步骤分析 ===", flush=True)
if '2' in body and '授权' in body and '授权信息' in body:
    print("在步骤2: 授权作品", flush=True)
    
    # 先处理艺人信息 - 选无主页链接
    if '有主页链接' in body:
        print("\n点击「有主页链接」切换为「无主页链接」", flush=True)
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
        # 选无主页链接
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '无主页链接') {
                    all[i].scrollIntoView({behavior:'instant', block:'center'});
                    all[i].focus();
                    all[i].click();
                    return;
                }
            }
        })();
        """)
        time.sleep(2)
    
    # 再处理封面 - 智能封面
    print("\n处理封面...", flush=True)
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
    
    body2 = P.ele('tag:body').text
    if '一键生成' in body2:
        print("弹窗出现，点击「一键生成封面」", flush=True)
        P.run_js("""
        (function() {
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                if (all[i].textContent && all[i].textContent.trim() === '一键生成封面') {
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
        time.sleep(5)
        
        body3 = P.ele('tag:body').text
        if '使用封面' in body3:
            print("封面已生成，点击「使用封面」", flush=True)
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
    
    # 点击下一步进入步骤3
    print("\n点击「下一步」进入签署协议...", flush=True)
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
    time.sleep(6)
    
    body4 = P.ele('tag:body').text
    print(f"点击后页面 (前2000):", flush=True)
    print(body4[:2000], flush=True)
    
    # 检查是否有 iframe / 合同相关
    pages = __import__('requests').get('http://localhost:9223/json').json()
    for p in pages:
        url = p.get('url', '')
        if 'letsign' in url or 'summon' in url:
            print(f"\n✅ 发现新页面: {p['title'][:30]} | {url[:80]}", flush=True)
else:
    print("不在步骤2，检查页面状态...", flush=True)
    print(body[:2000], flush=True)
