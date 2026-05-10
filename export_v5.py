"""导出v5 - 正确选择器"""
import sys, time, os, signal
from DrissionPage import ChromiumPage

# ── 信号处理：收到SIGTERM时杀Chrome再退出 ──
def _cleanup(signum, frame):
    print("\n⚠️ 收到暂停信号，清理 Chrome 进程...", flush=True)
    os.system("lsof -ti :9223 | xargs kill -9 2>/dev/null")
    os._exit(0)
signal.signal(signal.SIGTERM, _cleanup)
signal.signal(signal.SIGINT, _cleanup)

P = ChromiumPage(addr_or_opts="127.0.0.1:9223")

def js(code, d=None):
    for _ in range(2):
        try: return P.run_js(code)
        except:
            try: P.handle_alert(accept=True)
            except: pass
            time.sleep(1)
    return d

# 先处理任何残留弹窗 - 多重处理
for _ in range(3):
    try:
        P.handle_alert(accept=True)
        print("✅ 清除弹窗", flush=True)
        time.sleep(0.5)
    except:
        break
time.sleep(1)

# 用JS导航避免beforeunload弹窗阻塞
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create'")
time.sleep(5)

song = sys.argv[1] if len(sys.argv) > 1 else "迷音"
print(f"=== 导出 {song} ===", flush=True)

# 1. 作曲页 -> 点素材（用JS dispatchEvent，DrissionPage .click()有时不触发SPA）
# 确认在创作页
if 'create' not in P.url:
    P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create'")
    time.sleep(5)
# 等页面加载
time.sleep(2)
js(f"""(function(){{var items=document.querySelectorAll('[class*=\"titleRow\"]');for(var i=0;i<items.length;i++){{if(items[i].textContent.includes(\"{song}\")){{['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(t){{items[i].dispatchEvent(new PointerEvent(t,{{bubbles:true,cancelable:true}}))}});return 'clicked'}}}}return'not found'}})()""")
time.sleep(3)
print("1. 素材✅", flush=True)

# 2. AI编辑 (button class: aiEditButton)
js("""document.querySelectorAll('button[class*="aiEditButton"]').forEach(b=>{b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0,view:window,button:0}))})""")
time.sleep(3)
print("2. AI编辑✅", flush=True)

# 3. 去AI编辑器 (button class: primaryBtn) - 先滚到可见再点击
print("3. 去AI编辑器...", flush=True)
js("""document.querySelector('button[class*="primaryBtn"]')?.scrollIntoView({behavior:"instant",block:"center"})""")
time.sleep(1)
for _click_attempt in range(3):
    js("""document.querySelectorAll('button[class*="primaryBtn"]').forEach(b=>{b.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new PointerEvent(t,{bubbles:!0,cancelable:!0}))})})""")
    time.sleep(6)
    if 'playground' in P.url:
        break
    print(f"  重试... ({P.url[:50]})", flush=True)
js("window.onbeforeunload=null;window.alert=function(){}")
print(f"  编辑器 {P.url[:60]}✅", flush=True)

# 4. 等歌曲加载完成（关键：导出按钮需要加载完成才会激活）
print("4. 等待编辑器完全加载...", flush=True)
time.sleep(10)

# 5. 点击导出 (semi-button-secondary, 文本=导出)
print("4. 导出...", flush=True)
js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出'){['mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new MouseEvent(t,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
time.sleep(5)

has = js("return document.body.textContent.includes('并轨导出')", False)
if not has:
    print("  再点一次...", flush=True)
    js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出')b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0}))})""")
    time.sleep(5)
    has = js("return document.body.textContent.includes('并轨导出')", False)

print(f"5. 弹窗: {'✅' if has else '❌'}", flush=True)

if has:
    # 6. 改歌名
    js(f"""document.querySelectorAll('input').forEach(inp=>{{if(inp.value.includes('新项目')){{inp.disabled=false;inp.removeAttribute('disabled');Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(inp,'{song}');inp.dispatchEvent(new Event('input',{{bubbles:!0}}));inp.dispatchEvent(new Event('change',{{bubbles:!0}}))}}}})""")
    print("6. 改歌名✅", flush=True)
    time.sleep(1)
    
    # 7. 确认导出按钮
    print("7. 确认导出...", flush=True)
    js("""document.querySelectorAll('button.semi-button').forEach(b=>{const t=b.textContent.trim();if(t==='导出'||t==='并轨导出'||t==='确认导出'){['mousedown','mouseup','click'].forEach(tt=>{b.dispatchEvent(new MouseEvent(tt,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
    
    # 8. 等导出
    for i in range(30):
        time.sleep(3)
        if 'assets' in P.url:
            print(f"✅ 导出完成! 跳转到资产页", flush=True)
            break
        if i % 5 == 0:
            print(f"   导出中... ({i*3}s)", flush=True)
    else:
        print(f"⏰ 超时 URL: {P.url[:60]}", flush=True)

# 9. 资产页验证
time.sleep(3)
# 用JS导航到资产页（避免beforeunload弹窗）
P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets';")
time.sleep(5)
ok = js(f"return document.body.textContent.includes('{song}')", False)
print(f"结果: {'✅' if ok else '❌'} {song}", flush=True)
if not ok:
    P.get_screenshot(path=f"./temp_{song}_fail.png")
