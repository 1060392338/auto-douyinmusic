"""批量导出剩余歌曲 - 端口9222"""
import sys, time, os
from DrissionPage import ChromiumPage, ChromiumOptions

SONGS = ["杂乱思绪", "无章", "无序歌", "星落肩头", "空白页"]

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def js(P, code, d=None):
    for _ in range(2):
        try: return P.run_js(code)
        except:
            try: P.handle_alert(accept=True)
            except: pass
            time.sleep(1)
    return d

# 初始化浏览器
co = ChromiumOptions()
co.set_local_port(9222)
co.set_user_data_path(os.path.expanduser("~/.hermes/auto-douyinmusic/data/douyin_music/default/chrome_data"))
co.set_argument("--window-position=0,0")
co.set_argument("--window-size=1920,1080")
P = ChromiumPage(co)

log("浏览器已连接")

def export_one(song):
    log(f"\n{'='*50}\n🎵 {song}\n{'='*50}")
    
    # 清弹窗
    for _ in range(3):
        try: P.handle_alert(accept=True); time.sleep(0.3)
        except: break
    
    # 导航到作曲页
    P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create'")
    time.sleep(8)
    
    # 1. 点素材（歌名）
    code = f"""(function(){{var items=document.querySelectorAll('[class*="titleRow"]');for(var i=0;i<items.length;i++){{if(items[i].textContent.includes("{song}")){{['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(t){{items[i].dispatchEvent(new PointerEvent(t,{{bubbles:true,cancelable:true}}))}});return 'clicked'}}}}return'not found'}})()"""
    r = P.run_js(code)
    log(f"1. 素材: {r}")
    time.sleep(3)
    
    # 2. AI编辑
    P.run_js("""document.querySelectorAll('button[class*="aiEditButton"]').forEach(b=>{b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0,view:window,button:0}))})""")
    time.sleep(3)
    log("2. AI编辑 ✅")
    
    # 3. 去AI编辑器
    P.run_js("""document.querySelector('button[class*="primaryBtn"]')?.scrollIntoView({behavior:"instant",block:"center"})""")
    time.sleep(1)
    for attempt in range(3):
        P.run_js("""document.querySelectorAll('button[class*="primaryBtn"]').forEach(b=>{b.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new PointerEvent(t,{bubbles:!0,cancelable:!0}))})})""")
        time.sleep(6)
        if 'playground' in P.url:
            break
        log(f"  重试... {P.url[:60]}")
    P.run_js("window.onbeforeunload=null;window.alert=function(){}")
    log(f"3. 编辑器: {P.url[:80]}")
    
    # 4. 等编辑器加载
    log("4. 等待编辑器加载...")
    time.sleep(12)
    
    # 5. 点导出
    P.run_js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出'){['mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new MouseEvent(t,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
    time.sleep(5)
    
    has = P.run_js("return document.body.textContent.includes('并轨导出')")
    if not has:
        log("  再点一次导出...")
        P.run_js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出')b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0}))})""")
        time.sleep(5)
        has = P.run_js("return document.body.textContent.includes('并轨导出')")
    log(f"5. 弹窗: {'✅' if has else '❌'}")
    
    if has:
        # 6. 改歌名
        P.run_js(f"""(function(){{var inps=document.querySelectorAll('input');for(var i=0;i<inps.length;i++){{if(inps[i].value.includes('新项目')){{inps[i].disabled=false;inps[i].removeAttribute('disabled');Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(inps[i],'{song}');inps[i].dispatchEvent(new Event('input',{{bubbles:!0}}));inps[i].dispatchEvent(new Event('change',{{bubbles:!0}}))}}}})()""")
        log("6. 改歌名 ✅")
        time.sleep(1)
        
        # 7. 确认导出
        P.run_js("""document.querySelectorAll('button.semi-button').forEach(b=>{const t=b.textContent.trim();if(t==='导出'||t==='并轨导出'||t==='确认导出'){['mousedown','mouseup','click'].forEach(tt=>{b.dispatchEvent(new MouseEvent(tt,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
        log("7. 确认导出...")
        
        # 8. 等导出
        for i in range(40):
            time.sleep(3)
            if 'assets' in P.url:
                log(f"✅ 导出完成 → 资产页")
                return True
            if i % 5 == 0:
                log(f"   导出中... ({i*3}s)")
        log(f"⏰ 超时 URL: {P.url[:60]}")
        return False
    
    # 没弹窗的话导航到资产页验证
    P.run_js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
    time.sleep(5)
    ok = P.run_js(f"return document.body.textContent.includes('{song}')")
    log(f"结果: {'✅' if ok else '❌'} {song}")
    return ok

# 批量执行
results = {}
for song in SONGS:
    try:
        ok = export_one(song)
        results[song] = "✅" if ok else "❌"
    except Exception as e:
        results[song] = f"💥 {e}"
        log(f"💥 {song}: {e}")

log(f"\n{'='*50}")
log("📊 批量导出结果:")
for s, r in results.items():
    log(f"  {r} {s}")

log("脚本完成，浏览器未关闭")
