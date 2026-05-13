#!/usr/bin/env python3
"""批量导出5首歌曲 - 端口9222"""
import sys, time
from DrissionPage import ChromiumPage

SONGS = ["杂乱思绪", "无章", "无序歌", "星落肩头", "空白页"]

def log(msg):
    print(msg, flush=True)

P = ChromiumPage(addr_or_opts="127.0.0.1:9222")

def js(code, d=None):
    for _ in range(2):
        try: return P.run_js(code)
        except:
            try: P.handle_alert(accept=True)
            except: pass
            time.sleep(1)
    return d

for i, song in enumerate(SONGS):
    log(f"\n{'='*50}\n[{i+1}/5] 🎵 {song}\n{'='*50}")
    
    # 清弹窗
    for _ in range(3):
        try: P.handle_alert(accept=True); time.sleep(0.2)
        except: break
    
    # 导航到作曲页
    js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/create'")
    time.sleep(8)
    
    # 1. 点素材
    r = js(f"""(function(){{var items=document.querySelectorAll('[class*="titleRow"]');for(var i=0;i<items.length;i++){{if(items[i].textContent.includes("{song}")){{['pointerdown','pointerup','mousedown','mouseup','click'].forEach(function(t){{items[i].dispatchEvent(new PointerEvent(t,{{bubbles:true,cancelable:true}}))}});return 'clicked'}}}}return 'not found'}})()""")
    log(f"  1.素材: {r}")
    time.sleep(3)
    
    # 2. AI编辑
    js("""document.querySelectorAll('button[class*="aiEditButton"]').forEach(b=>{b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0,view:window,button:0}))})""")
    time.sleep(3)
    log("  2.AI编辑 ✅")
    
    # 3. 去AI编辑器
    js("""document.querySelector('button[class*="primaryBtn"]')?.scrollIntoView({behavior:"instant",block:"center"})""")
    time.sleep(1)
    for att in range(3):
        js("""document.querySelectorAll('button[class*="primaryBtn"]').forEach(b=>{b.focus();['pointerdown','pointerup','mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new PointerEvent(t,{bubbles:!0,cancelable:!0}))})})""")
        time.sleep(6)
        if 'playground' in P.url:
            break
        log(f"    重试... ({P.url[:50]})")
    js("window.onbeforeunload=null;window.alert=function(){}")
    ok3 = 'playground' in P.url
    log(f"  3.编辑器: {'✅' if ok3 else '❌'}")
    
    # 4. 等加载
    log("  4.等待加载...")
    time.sleep(15)
    
    # 5. 点导出
    js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出'){['mousedown','mouseup','click'].forEach(t=>{b.dispatchEvent(new MouseEvent(t,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
    time.sleep(5)
    
    has = js("return document.body.textContent.includes('并轨导出')", False)
    if not has:
        log("    再点导出...")
        js("""document.querySelectorAll('button.semi-button-secondary').forEach(b=>{if(b.textContent.trim()==='导出')b.dispatchEvent(new MouseEvent('click',{bubbles:!0,cancelable:!0}))})""")
        time.sleep(5)
        has = js("return document.body.textContent.includes('并轨导出')", False)
    log(f"  5.弹窗: {'✅' if has else '❌'}")
    
    if has:
        # 6. 改歌名
        js(f"""(function(){{var inps=document.querySelectorAll('input');for(var i=0;i<inps.length;i++){{if(inps[i].value.includes('新项目')){{inps[i].disabled=false;inps[i].removeAttribute('disabled');var d=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value');d.set.call(inps[i],'{song}');inps[i].dispatchEvent(new Event('input',{{bubbles:!0}}));inps[i].dispatchEvent(new Event('change',{{bubbles:!0}}))}}}})()""")
        log("  6.改歌名 ✅")
        time.sleep(1)
        
        # 7. 确认导出
        js("""document.querySelectorAll('button.semi-button').forEach(b=>{var t=b.textContent.trim();if(t==='导出'||t==='并轨导出'||t==='确认导出'){['mousedown','mouseup','click'].forEach(tt=>{b.dispatchEvent(new MouseEvent(tt,{bubbles:!0,cancelable:!0,view:window,button:0}))})}})""")
        log("  7.确认导出...")
        
        for j in range(50):
            time.sleep(3)
            if 'assets' in P.url:
                log(f"  ✅ 导出完成 ({j*3}s)")
                break
            if j % 5 == 0:
                log(f"    导出中... ({j*3}s)")
        else:
            log(f"  ⏰ 超时 {P.url[:60]}")
    
    # 验证
    js("window.onbeforeunload=null;window.location.href='https://music.douyin.com/studio/assets'")
    time.sleep(5)
    ok = js(f"return document.body.textContent.includes('{song}')", False)
    log(f"  📊 结果: {'✅ 在资产页' if ok else '❌ 不在资产页'}")

log("\n" + "="*50)
log("🏁 批量导出完成！")
