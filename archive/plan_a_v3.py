"""CDP + DrissionPage 混合方案"""
import time, json, requests, websocket

# 1. 用 CDP 清理所有有弹窗的页面
bws = requests.get('http://localhost:9223/json/version').json()['webSocketDebuggerUrl']
b = websocket.create_connection(bws, timeout=5)

# 获取所有 target
b.send(json.dumps({'id':1, 'method':'Target.getTargets', 'params':{}}))
resp = json.loads(b.recv())
targets = resp.get('result',{}).get('targetInfos',[])

print(f"清理前 {len(targets)} 个页面:", flush=True)
for t in targets:
    print(f"  {t['title'][:30]} | {t['url'][:60]}", flush=True)
    
    # 对每个非 studio 页面，尝试处理弹窗
    ws_p = websocket.create_connection(t['webSocketDebuggerUrl'], timeout=5)
    try:
        cid = 1
        ws_p.send(json.dumps({'id':cid, 'method':'Page.getJavaScriptDialogInfo', 'params':{}}))
        r = json.loads(ws_p.recv())
        if r.get('result',{}).get('hasDialog'):
            print(f"    ⚠️ 有弹窗，接受中...", flush=True)
            cid += 1
            ws_p.send(json.dumps({'id':cid, 'method':'Page.handleJavaScriptDialog', 'params':{'accept':True}}))
            json.loads(ws_p.recv())
            print(f"    ✅ 已处理", flush=True)
    except:
        pass
    finally:
        ws_p.close()

b.close()
time.sleep(2)

# 2. 现在用 DrissionPage 连接 - 应该没有弹窗了
print("\n连接 DrissionPage...", flush=True)
from DrissionPage import ChromiumPage
P = ChromiumPage(addr_or_opts='127.0.0.1:9223')
time.sleep(2)

# 禁用弹窗
P.run_js("window.onbeforeunload=null;")
print("✅ 弹窗已禁用", flush=True)

# 导航到发布页
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/console/complete-publish?enter_from=astra&issuedId=7638146107109231379';")
time.sleep(6)
P.run_js("window.onbeforeunload=null;")

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
    print("❌ 发布页加载失败", flush=True)
    exit()

text = body.text
print(f"✅ 发布页, 文本长度:{len(text)}", flush=True)

# 智能封面
print("智能封面...", flush=True)
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
    print("✅ 一键生成封面...", flush=True)
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
        print("✅ 使用封面...", flush=True)
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
        
        # 检查弹窗是否还开着
        t3b = P.ele('tag:body', timeout=5).text
        if '使用封面' in t3b and '取消' in t3b:
            print("弹窗未关，点击取消...", flush=True)
            P.run_js("""
            window.onbeforeunload=null;
            document.querySelectorAll('*').forEach(function(el) {
                var t = (el.textContent || '').trim();
                if (t === '取消' || t === '关闭') {
                    el.click();
                }
            });
            """)
            time.sleep(3)

# 关闭所有弹窗
print("关闭弹窗...", flush=True)
P.run_js("""
window.onbeforeunload=null;
document.querySelectorAll('*').forEach(function(el) {
    var t = (el.textContent || '').trim();
    if ((t === '取消' || t === '关闭' || t === 'X') && el.offsetParent !== null) {
        el.click();
    }
});
""")
time.sleep(2)

# 滚动到底部
P.run_js("window.onbeforeunload=null;window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# 下一步
print("点击下一步...", flush=True)
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

print(f"URL: {P.url[:80]}", flush=True)
pages = requests.get('http://localhost:9223/json').json()
print(f"页面 ({len(pages)}):", flush=True)
for p in pages:
    url = p.get('url','')
    print(f"  {p['title'][:30]} | {url[:80]}", flush=True)
    if 'letsign' in url:
        print(f"  ✅ 合同页!", flush=True)

try:
    t4 = P.ele('tag:body', timeout=5).text
    print(f"\n底部600: ...{t4[-600:]}", flush=True)
    for kw in ['批量签署','意愿认证','获取验证码','合同签署']:
        if kw in t4:
            print(f"  ✅ {kw}", flush=True)
except:
    pass

print("\n✅ 完成", flush=True)
